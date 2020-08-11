import requests
import getpass
import datetime
import pandas as pd
import re
import os
import pytz
from bs4 import BeautifulSoup
import logging
import io

from scipy.io import netcdf_file

from eugreendeal.settings import MEDIA_ROOT
from dataingestor.DataSource import DataSource
from airpollution.models.models_copernicus import SatelliteImageFiles
from airpollution.models.models_pollutants import Pollutant, Target

# Global variable for the directory where NC files are saved
TARGET_DIR = os.path.join(MEDIA_ROOT, 'media', 'satellite_data')


class CopernicusDataSource(DataSource):

    def __init__(self, logger: logging.Logger, name: str, description: str = None, token: str = None):
        DataSource.__init__(self, name, description)
        if token is None:
            self._token = self.set_token()
        else:
            self._token = token

        if logger is None:
            self.logger = logging.getLogger("load_satellite_images")
            self.logger.setLevel(level=logging.ERROR)
        else:
            self.logger = logger

    def load_data(self, **kwargs) -> None:

        # ----------------------
        # SET DEFAULT VALUES WHERE MISSING
        # parse kwargs

        target_dir = kwargs.get('target_dir')
        if not target_dir:
            target_dir = TARGET_DIR

        category = kwargs.get('category')
        if not category:
            category = ['ANALYSIS']

        levels = kwargs.setdefault('levels')
        if not levels:
            levels = ['ALLLEVELS']

        reference_time = kwargs.setdefault('reference_time')
        if not reference_time:
            yesterday = (datetime.datetime.today() - datetime.timedelta(1)).isoformat().split('T')[0]
            reference_time = f"{yesterday}T00:00:00Z"
        # END SET DEFAULT VALUES
        # ----------------------

        self.logger.info(f"Collecting date: {reference_time}")

        # # retrieve data
        # self.logger.info(f"Saving files to: \n{target_dir}")
        # df = self.download_daily_files(token=token,
        #                                target_dir=target_dir,
        #                                category=category,
        #                                levels=levels,
        #                                reference_time=reference_time)
        #
        # # load into db
        # r_message = self.load_db_from_df(df)
        r_message = self._load_images_direct_to_db(reference_time)

        self.logger.info(r_message)

    def load_dummy_data(self):
        pass

    # def load_db_from_files(self, dirpath: str = TARGET_DIR, extension='.nc') -> str:
    #     df = self.create_df_from_dir(dirpath=dirpath, extension=extension)
    #     r_message = self.load_db_from_df(df)
    #     return r_message

    def set_token(self) -> str:
        """
        Generates a token based on userid and password from the Copernicus API service.
        This does not validate the userid/password combination.
        Any environment variable stored in COPERNICUS_ID and COPERNICUS_PW will be used to
        retrieve token.  A token
        :return: token string or None if error
        """

        t = os.environ.get("COPERNICUS_TOKEN")
        # if token is stored, return it
        if t:
            self._token = t
            return self._token

        # if user id and pw are available
        uid = os.environ.get("COPERNICUS_ID")
        pw = os.environ.get("COPERNICUS_PW")

        if not uid:
            print("A copernicus ID is required to download satellite data.")
            print("https://ads.atmosphere.copernicus.eu/user/register")
            uid = input("Copernicus User ID: ")
            os.environ.setdefault("COPERNICUS_ID", uid)
        if not pw:
            pw = getpass.getpass()
            os.environ.setdefault("COPERNICUS_PW", pw)

        url = f'https://geoservices.regional.atmosphere.copernicus.eu/services/GetAPIKey?username={uid}&password={pw}'
        token_response = requests.get(url)

        if token_response.status_code == 200:
            t = BeautifulSoup(token_response.text, 'html.parser').text
            self._token = t
            return self._token

        self.logger.error(f"No token returned: {token_response.status_code}")
        return ""

    #######################
    # SUPPORT FUNCTIONS
    #######################
    def _load_images_direct_to_db(self, reference_time: str) -> str:
        """
        Loads satellite image directly into the database.
        Only includes an average image for an entire day for pollutants with calendar year targets.
        :param reference_time: Time (format: YYYY-MM-DDT00:00:00Z) of the satellite images to load
        :return: None
        """

        # These must be fixed to get a daily average at the surface
        category = 'ANALYSIS'
        levels = 'SURFACE'
        pollutants = [x.get('pollutant_id') for x in Target.objects.all().values() if
                      x.get('measurement_id') == 'calendar_year']

        count = 0
        for p in pollutants:
            url = self._create_file_url(token=self._token,
                                        pollutant_key=p,
                                        reference_time=reference_time,
                                        category=category,
                                        levels=levels)

            rv = self._load_netcdf_record_from_url(url)
            count += rv

        return f"Loaded {count} satellite image records."

    def _load_netcdf_record_from_url(self, url: str) -> int:
        """
        Load the netcdf image and related data diretcly from the url.
        :param url: URL to eea data service for the desired image.
        :return: Number of records loaded.
        """

        self.logger.debug(f"Getting request from Copernicus ... ")
        r = requests.get(url)
        self.logger.debug(f"Request returned with status {r.status_code}")

        if r.status_code != 200:
            self.logger.error(f"{self._handle_web_error(r.status_code)}")
            self.logger.error(url)
            return 0
        else:
            try:
                # determine the filename
                fname = self._get_filename_from_cd(r.headers.get('content-disposition'))
                if fname is None:
                    yesterday = (datetime.datetime.today() - datetime.timedelta(1)).isoformat().split('T')[0]
                    fname = f"{yesterday}Z.nc"

            except Exception as e:
                print(f'Unable to get filename from url request. {e}')
                return 0

        # get parameters from the filename
        params = self.get_params_from_filepath(fname)

        # get in memory netcdf file object
        f = io.BytesIO(r.content)
        ds = netcdf_file(f)
        f.close()

        # determine pollutant in the file
        cop_pollutant = list(ds.variables.keys())[-1]
        pollutant_key = Pollutant.get(cop_pollutant)

        # determine date of the file
        year, month, day = params['year'], params['month'], params['day']

        # calculate the day average image
        surface_images = ds.variables.get(cop_pollutant).data[:, 0, :]
        surface_dayavg_image = surface_images.mean(axis=0)

        # determine record key from filename
        key = fname.split('/')[-1]

        # load data for record
        load_series = pd.Series({
            'key': key,
            'date': f"{year}-{month:2}-{day:2}",
            'date_time': datetime.datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.timezone("CET")),
            'pollutant': Pollutant.objects.get(pk=pollutant_key),
            'description': ds.title.decode(),
            'model': params['model'],
            'category': params['category'],
            'bbox_minlon': ds.variables.get('longitude').data.min(),
            'bbox_maxlon': ds.variables.get('longitude').data.max(),
            'bbox_minlat': ds.variables.get('latitude').data.min(),
            'bbox_maxlat': ds.variables.get('latitude').data.max(),
            'levels': [int(x) for x in ds.variables.get('level').data],
            'hours': [int(x) for x in ds.variables.get('time').data],
            'year': year,
            'month': month,
            'day': day,
            'image_shape': surface_dayavg_image.shape,
            'file_path': fname,
            'image': surface_dayavg_image.flatten()
        })

        try:
            img = " ".join([str(x) for x in load_series.image.flatten()])
            record = SatelliteImageFiles.objects.create(key=load_series.key,
                                                        date=load_series.date,
                                                        date_time=load_series.date_time,
                                                        pollutant=load_series.pollutant,
                                                        description=load_series.description,
                                                        model=load_series.model,
                                                        category=load_series.category,
                                                        bbox_minlon=load_series.bbox_minlon,
                                                        bbox_maxlon=load_series.bbox_maxlon,
                                                        bbox_minlat=load_series.bbox_minlat,
                                                        bbox_maxlat=load_series.bbox_maxlat,
                                                        levels=load_series.levels,
                                                        hours=load_series.hours,
                                                        year=load_series.year,
                                                        month=load_series.month,
                                                        day=load_series.day,
                                                        shape=" ".join([str(x) for x in load_series.image_shape]),
                                                        file_path=load_series.file_path,
                                                        image=img
                                                        )
            record.save()
            return 1

        except Exception as e:
            self.logger.error(f"{e}")
            return 0



    # def download_daily_files(self, token: str,
    #                          target_dir: str,
    #                          category: list,
    #                          levels: list,
    #                          reference_time: str,
    #                          pollutant_keys: list = []) -> pd.DataFrame:
    #     """
    #     Downloads all the pollutant satellite images for a selected date (reference_time).
    #     Return a dataframe with the info that should be loaded into DB.
    #     """
    #
    #     self.logger.info(
    #         "Starting download.  Downloads can take several minutes depending on Copernicus server traffic.")
    #
    #     # create empty dataframe to store info of data files downloaded (used to update DB)
    #     df = pd.DataFrame()
    #
    #     for c in category:
    #         for l in levels:
    #
    #             # get a valid list of the pollutants
    #             valid_pkeys = self.get_pollutant_keys(token, category=c, levels=l)
    #             p_keys = []
    #             if len(pollutant_keys) == 0:
    #                 p_keys = valid_pkeys
    #             else:
    #                 p_keys = list(set(pollutant_keys) & set(valid_pkeys))
    #
    #             # loop through each pollutant and download the file
    #             for p in tqdm(p_keys, desc='downloading satellite images'):
    #
    #                 # download file
    #                 fpath = self.download_pollutant_file(token=token,
    #                                                      pollutant_key=p,
    #                                                      target_dir=target_dir,
    #                                                      reference_time=reference_time,
    #                                                      category=c, levels=l)
    #                 if fpath == 'exists':
    #                     self.logger.error(f"File already exists. Skipping: {p} {c} {l} {reference_time}")
    #                     continue
    #
    #                 if not fpath:
    #                     self.logger.error(f"Unable to get file: {p} {c} {l} {reference_time}")
    #                     continue
    #
    #                 # create a record for the file
    #                 s = self.create_db_record_for_file(fpath)
    #
    #                 # add file record to database
    #                 df = df.append(s, ignore_index=True)
    #
    #     return df
    #
    # def download_pollutant_file(self,
    #                             token: str, target_dir: str,
    #                             pollutant_key: str, reference_time: str,
    #                             category: str, levels: str) -> str:
    #     """
    #     Downloads a pollutant netcdf file for a particular pollutant .
    #     If reference_time is not provided, the current file will be downloaded.
    #     Files from 30 days prior are available per API service.
    #     """
    #     # create a URL for the file download
    #     self.logger.debug("Creating file url ...")
    #     file_url = self._create_file_url(token, pollutant_key, reference_time=reference_time, category=category,
    #                                      levels=levels)
    #     self.logger.debug(f"URL Created: \n{file_url}")
    #
    #     # save file. defaults to media directory.  returns saved filepath
    #     self.logger.debug("Saving file ...")
    #     saved_filepath = self._save_file_from_url(file_url, target_dir=target_dir)
    #     self.logger.debug(f"Saved file: {saved_filepath}")
    #
    #     return saved_filepath

    def _create_file_url(self, token: str,
                         pollutant_key: str,
                         reference_time: str,
                         category: str,
                         levels: str,
                         times: str = None,
                         grid_size='0.1',
                         model='ENSEMBLE',
                         base_url='https://download.regional.atmosphere.copernicus.eu/services/CAMS50',
                         fileformat='NETCDF'
                         ) -> str:
        """
        Create an API URL based on arguments.
        :param token:ste - A Copernicus token.
        :param pollutant_key:str - A pollutant.  One of O3, CO, NO2, SO2 ,PM25 , PM10, PANS, NMVOC,NO,NH3.
        :param reference_time:str - The day from which the file URL will get images for. Format YYYY-MM-DDT00:00:00Z.  If blank, prior day's date is used.
        :param base_url:str - The base URL for the API call to download files with images.
        :param grid_size:str - Default=0.1.  The resolution of the resulting image map.  Not tested for values other than 0.1.
        :param model:str - The Copernicus model used.  One of ENSEMBLE, CHIMERE, EMEP, EURAD-IM, LOTOS-EUROS, MATCH, MOCAGE, SILAM.
        :param category:str - Forecast or actual data. FORECAST | ANALYSIS.
        :param levels:str - Surface or air levels.  One of SURFACE | ALLLEVELS
        :param times:str - Range of hours for maps returned in files. For ANALYSIS -24H-1H for forecast 0H24H | 25H48H | 49H72H |73H96H
        :param fileformat:str - Format of the returned file.  NETCDF | GRIB2
        """

        if not reference_time:
            yesterday = (datetime.datetime.today() - datetime.timedelta(1)).isoformat().split('T')[0]
            reference_time = f"{yesterday}T00:00:00Z"

        if not times:
            times = '-24H-1H' if category == 'ANALYSIS' else '0H24H'

        # check that times are reasonable for forecast cateogry
        if category == 'FORECAST':
            if times not in ['0H24H', '25H48H', '49H72H', '73H96H']:
                self.logger.error(
                    f"Forecast times of '{times}' not supported.  Select one of '0H24H', '25H48H', '49H72H', '73H96H'.")
                return None

        url = f'{base_url}?token={token}&grid={grid_size}&model={model}&package={category}_{pollutant_key}_{levels}&time={times}&referencetime={reference_time}&format={fileformat}'

        return url

    # def _save_file_from_url(self, uri: str, target_dir: str) -> str:
    #     """
    #     Will save the file from a url as the filename.
    #     If no save_path is provided, file is saved to the TARGET_DIR directory.
    #     """
    #     fpath = ""
    #
    #     # make the api request
    #     self.logger.debug(f"Getting request from Copernicus ... ")
    #     r = requests.get(uri)
    #     self.logger.debug(f"Request returned with status {r.status_code}")
    #
    #     if r.status_code != 200:
    #         self.logger.error(f"{self._handle_web_error(r.status_code)}")
    #         self.logger.error(uri)
    #         return None
    #     else:
    #         try:
    #             # determine the filename
    #             fname = self._get_filename_from_cd(r.headers.get('content-disposition'))
    #             if fname is None:
    #                 yesterday = (datetime.datetime.today() - datetime.timedelta(1)).isoformat().split('T')[0]
    #                 fname = f"{yesterday}Z.nc"
    #
    #             # create a full path to save file to
    #             fpath = os.path.join(target_dir, fname)
    #
    #             if os.path.isfile(fpath):
    #                 return 'exists'
    #
    #             with open(fpath, "wb") as f:
    #                 self.logger.info("Saving file ...")
    #                 f.write(r.content)
    #                 self.logger.info("File saved!")
    #             return fpath
    #         except Exception as e:
    #             self.logger.error(f"Error saving file. {e}")
    #             self.logger.error(f"\t{fpath}")
    #             return None

    @staticmethod
    def _get_filename_from_cd(cd):
        """
        Get filename from content-disposition.
        https://www.codementor.io/@aviaryan/downloading-files-from-urls-in-python-77q3bs0un
        """
        if not cd:
            return None
        fname = re.findall('filename=(.+)', cd)

        if len(fname) == 0:
            return None

        fname = fname[0]

        # removed quotation marks at beginning and end
        if fname[0] == '"':
            fname = fname[1:]
        if fname[-1] == '"':
            fname = fname[:-1]

        return fname

    # def create_db_record_for_file(self, filepath) -> pd.Series:
    #     """
    #     Create a db record based on the filepath.
    #     :param filepath - the full path of the file for which to create a db entry.
    #     """
    #
    #     # retrieve the file and extract paramters to save to database
    #     ds = netCDF4.Dataset(filepath)
    #     params = self.get_params_from_netcdf(ds)
    #
    #     # save to storage
    #     s = pd.Series(data=np.array(list(params.values())), index=list(params.keys()))
    #     s = s.append(pd.Series(filepath, index=['filename']))
    #     s = s.append(pd.Series(filepath.split('/')[-1], index=['key']))
    #
    #     return s

    # def get_params_from_netcdf(self, ds: netCDF4._netCDF4.Dataset) -> dict:
    #     """
    #     Returns a dict of descriptive parameters for a dataset.  Relies on data from the filename.
    #     :param ds - A netcdf4 dataset of Copernicus satellite image data.
    #     """
    #     locators = ['longitude', 'latitude', 'level', 'time']
    #     pollutant = [k for k in ds.variables.keys() if k not in locators][0]
    #
    #     # find the date of the file
    #     if 'FORECAST' in ds.ncattrs():
    #         date_field = ds.FORECAST
    #     elif 'ANALYSIS' in ds.ncattrs():
    #         date_field = ds.ANALYSIS
    #     else:
    #         date_field = self.get_date_from_filepath(ds.filepath())
    #
    #     date = re.findall('(\d{8})', date_field)[0]
    #     year, month, day = int(date[:4]), int(date[4:6]), int(date[6:8])
    #
    #     # get the true pollutant key value
    #     fname_params = self.get_params_from_filepath(ds.filepath())
    #
    #     rv = {'description': ds.title,
    #           'category': fname_params['category'],
    #           'pollutant_key': fname_params['pollutant'],
    #           'pollutant': pollutant,
    #           'model': fname_params['model'],
    #           'bbox_minlon': min(ds['longitude'][:]),
    #           'bbox_maxlon': max(ds['longitude'][:]),
    #           'bbox_minlat': min(ds['latitude'][:]),
    #           'bbox_maxlat': max(ds['latitude'][:]),
    #           'levels': [int(x) for x in list(ds['level'][:].data)],
    #           'hours': [int(x) for x in list(ds['time'][:].data)],
    #           'date': f"{year}-{month:02}-{day:02}",
    #           'year': year,
    #           'month': month,
    #           'day': day,
    #           'shape': ds[pollutant][:].shape}
    #
    #     return rv
    #
    # def get_date_from_filepath(self, filepath: str) -> str:
    #     """
    #     Returns an 8-digit date from a filepath: YYYYMMDD
    #     """
    #     date = self.get_params_from_filepath(filepath).get('date')[0:8]
    #
    #     return date

    @staticmethod
    def get_params_from_filepath(filepath) -> dict:
        """
        Return a dictionary of parameters from a netcdf filename.
        :param filepath - full path of netcdf file which the file's name will be parsed.
        """
        filename = filepath.split('/')[-1]
        _, _, details = filename.split(',')
        model, cateogry, levels, pollutant, rest = details.split('+')
        time_range, _, _, rest = rest.split('_')
        date, _ = rest.split('.')
        year = date[:4]
        month = date[4:6]
        day = date[6:8]
        hour = date[8:10]
        minute = date[10:12]
        sec = date[12:]

        rv = {'model': model,
              'category': cateogry,
              'levels': levels,
              'pollutant': pollutant,
              'timerange': time_range,
              'date': date,
              'year': year,
              'month': month,
              'day': day,
              'hour': hour,
              'minute': minute,
              'second': sec}

        return rv

    def _handle_web_error(self, status_code) -> str:
        """
        Support function to handle web errors
        :param status_code - HTML status code returned from a request.
        """

        err_dict = {200: "200: OK",
                    400: "400: Parameter missing, parameter model is mandatory",
                    401: "401: Parameter token is invalid. Please specify &token=YOUR_KEY",
                    403: "403: Values of parameters are wrong. Possible unsupported date.",
                    404: "404: Not Found",
                    503: "503: Server error. Try again later."}

        return err_dict.setdefault(status_code, f"{status_code}: unknown error status code.")

    # def get_pollutant_keys(self, token, category, levels, vc=None) -> list:
    #     """
    #     Return the current list of pollutant keys.
    #     :param levels:
    #     :param category:
    #     :param token - a Copernicus token.
    #     :param vc - a view capability dictionary retrieved from _get_view_capabilities() function.
    #     """
    #     FORECAST_ALLLEVELS = ['O3', 'CO', 'NO2', 'SO2', 'PM25', 'PM10', 'PANS', 'NMVOC', 'NO', 'NH3']
    #     FORECAST_SURFACE = ['O3', 'CO', 'NO2', 'SO2', 'PM25', 'PM10', 'BIRCHPOLLEN', 'OLIVEPOLLEN', 'GRASSPOLLEN',
    #                         'RAGWEEDPOLLEN']
    #     ANALYSIS_ALLLEVELS = ['O3', 'CO', 'NO2', 'SO2', 'PM25', 'PM10', 'PANS', 'NMVOC', 'NO', 'NH3']
    #     ANALYSIS_SURFACE = ['O3', 'CO', 'NO2', 'SO2', 'PM25', 'PM10', 'PANS', 'NMVOC', 'NO', 'NH3']
    #
    #     if category == 'FORECAST':
    #         if levels == 'ALLLEVELS':
    #             return FORECAST_ALLLEVELS
    #         else:
    #             return FORECAST_SURFACE
    #
    #     elif category == 'ANALYSIS':
    #         if levels == 'ALLLEVELS':
    #             return ANALYSIS_ALLLEVELS
    #         else:
    #             return ANALYSIS_SURFACE
    #     else:
    #         self.logger.info(f"Pollutant keys cannot be determined: {category} {levels}")
    #         return None
    #
    # def _get_filenames_in_dir(self, directory: str, extension: str = '.nc') -> list:
    #     """
    #     Returns a list of filenames in a directory.
    #     :param directory: root directory from which to start search.
    #     :param extension: Looks for files with the supplied extension.  Defaults to '.nc'
    #     :return: List of all files meeting the extension criteria under the provided directory.
    #     """
    #
    #     # check the dir is a directory
    #     if not os.path.isdir(directory):
    #         self.logger.error(f"'{directory}' is not a directory.")
    #         return []
    #
    #     # walk through root and keep all .nc files
    #     rv = []
    #     for par, dirs, files in os.walk(directory):
    #
    #         for f in files:
    #             fname, ext = os.path.splitext(f)
    #             if ext == extension:
    #                 rv.append(os.path.join(par, f))
    #
    #     return rv
    #
    # def _create_df_from_files(self, filenames: list) -> pd.DataFrame:
    #     """
    #     Creates a Pandas dataframe based on files in the list of file names provided.
    #     :param filenames: List of file names.
    #     :return: DataFrame that contains the parameters of each file in the provided list.
    #     """
    #     df = pd.DataFrame()
    #
    #     for fpath in filenames:
    #         # create a record for the file
    #         s = self.create_db_record_for_file(fpath)
    #
    #         # add file record to database
    #         df = df.append(s, ignore_index=True)
    #
    #     return df
    #
    # def create_df_from_dir(self, dirpath: str, extension='.nc') -> pd.DataFrame:
    #     """
    #     Create a dataframe of file parameters based on a provided root directory.
    #     :param extension: file extension to look for when adding items to dataframe
    #     :param dirpath: Path to directory from which to start searching for files.
    #     :return:
    #     """
    #     filenames = self._get_filenames_in_dir(dirpath, extension=extension)
    #
    #     df = self._create_df_from_files(filenames)
    #
    #     return df
    #
    # def load_db_from_df(self, df: pd.DataFrame) -> str:
    #     """
    #     Load the DB based on a dataframe returned when downloading files using
    #     the function download_daily_files().
    #
    #     :return: None
    #     """
    #     for obj in SatelliteImageFiles.objects.all():
    #         obj.delete()
    #
    #     count = 0
    #     tz = pytz.timezone("CET")
    #     for idx, row in tqdm(df.iterrows(), desc='loading images'):
    #         shape = ",".join(
    #             str(x) for x in row['shape'])  # shape is reserved - returns series shape not value of shape
    #         levels = ",".join(str(x) for x in np.ravel(row.levels))
    #         hours = ",".join(str(x) for x in np.ravel(row.hours))
    #
    #         try:
    #             p = Pollutant.objects.get(pk=row.pollutant_key)
    #         except ObjectDoesNotExist as e:
    #             self.logger.error(e)
    #             self.logger.error(f"Pollutant not found: {row.pollutant_key}")
    #             continue
    #
    #         try:
    #             record = SatelliteImageFiles.objects.create(key=row.key,
    #                                                         date=row.date,
    #                                                         date_time=datetime.datetime(year=int(row.year),
    #                                                                                     month=int(row.month),
    #                                                                                     day=int(row.day), tzinfo=tz),
    #                                                         pollutant=p,
    #                                                         description=row.description,
    #                                                         model=row.model,
    #                                                         category=row.category,
    #                                                         bbox_minlon=row.bbox_minlon,
    #                                                         bbox_maxlon=row.bbox_maxlon,
    #                                                         bbox_minlat=row.bbox_minlat,
    #                                                         bbox_maxlat=row.bbox_maxlat,
    #                                                         levels=levels,
    #                                                         hours=hours,
    #                                                         year=row.year,
    #                                                         month=row.month,
    #                                                         day=row.day,
    #                                                         shape=shape,
    #                                                         file_path=row.filename)
    #             record.save()
    #             count += 1
    #
    #         except Exception as e:
    #             self.logger.error(e)
    #
    #     return f"Loaded {count} images.".format(count=count)
