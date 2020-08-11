"""
Author: Mark McDonald
This model will hold readings from observation stations
"""
import datetime
import logging
import string

import pandas as pd
import pytz
import requests
from django.core.exceptions import ObjectDoesNotExist
from tqdm import tqdm

from airpollution.models import EU_ISOCODES, Pollutant, ObservationStation, EUCountries, ObservationStationReading
from dataingestor.DataSource import DataSource


class ReadingDataSource(DataSource):

    def __init__(self, name: str, logger: logging.Logger, description: str = None):
        DataSource.__init__(self, name, description)
        self.logger = logger

    def load_data(self, dummy: bool = False, **kwargs) -> dict:
        """
        Loads a year at a time only.  Will first delete all entries for the year
        and country if they already exist.  Year_from and Year_to are ignore if since_date provided.
        :param dummy: Boolean.  If True, limited random records are loaded.
        :param kwargs: Supports, year_from:str, year_to:str, since_date:str, country_codes:list
        :return: If error, return dict with error description.
        """
        # read and load one year at a time or days since a since_date
        year_from = int(kwargs.get('year_from', 0))
        year_to = int(kwargs.get('year_to', 0))
        since_date = kwargs.get('since_date', '')  # YYYY-MM-DD
        country_codes = kwargs.get('country_codes', [''])
        p_list = kwargs.get('pollutants', '')
        stations = kwargs.get('stations', '')
        month = kwargs.get('month', 0)

        # check that either from/to years are provided OR a since_date
        # since date takes precendence if all are supplied
        if since_date == '' and year_from == '' and year_to == '':
            err_text = f"Either from/to years OR since_date argument must be provided."
            self.logger.error(err_text)
            return {'error': err_text}

        if since_date is not None and since_date != '':
            year_from = int(since_date.split('-')[0])
            year_to = int(since_date.split('-')[0])
            self.logger.info(
                f"Loading observation station readings since {since_date}")
        elif month != 0:
            self.logger.info(f"Loading observation station readings .. for month:{month} year:{year_to}")
        else:
            self.logger.info(f"Loading observation station readings .. from {year_from} to {year_to}")

        # if no countries provided, select EU countries only
        if len(country_codes) == 0:
            country_codes = EU_ISOCODES

        # get a list of pollutant key strings
        # if no specific pollutants provided, get all that are supported
        # this retrieves a list of the pollutant keys used for the EEA rest request
        if p_list is '':
            # ['PM2.5', 'PM10', 'O3', 'NO2', 'CO', 'SO2']
            pollutants = Pollutant.get_observation_pollutants().keys()

        # a pollutant list was provided - get the supported pollutants in the EEA key format
        else:
            try:
                p_objs = Pollutant.objects.filter(key__in=p_list)
                pollutants = [x.observation_key for x in p_objs]
            except Exception as e:
                self.logger.info(f"Pollutants not supported: {p_list}")
                return {"error": f"Pollutants not supported: {p_list}"}

        # if stations are provided, load by stations
        if stations != '':
            self._load_by_stations(stations, pollutants, year_from, year_to, since_date, month)

        # if stations are not provided, use countries
        else:
            self._load_by_countries(country_codes, pollutants, year_from, year_to, since_date, month)

        self.logger.info("Done loading Observation Readings.")

    def load_dummy_data(self, **kwargs):
        """
        This will return a series of arguments that can be passes to load_data()
        which will load a limited set of data.  This is done by selecting a limited number
        of data collection stations to load.
        :param kwargs:
        :return:
        """
        self.logger.info("Loading in DUMMY mode.  Restricted data quantity will be loaded.")

        # get a restricted set of stations
        level = kwargs.get('level', 0)
        n = kwargs.get('n', 1)
        frac = kwargs.get('frac', None)

        countries = kwargs.get('country_codes', None)

        stations = ObservationStation.get_stratified_stations(level=level, n=n, frac=frac, countries=countries)
        kwargs.update({'stations': stations})

        self.logger.info(f"Selected {len(stations)} stations to load")

        # run load process
        self.load_data(**kwargs)

    def _load_by_stations(self, stations, pollutants, year_from, year_to, since_date, month):

        err_list = []
        for s in tqdm(stations, desc='stations', leave=True):
            c = ObservationStation.get_country_code(s)
            for p in tqdm(pollutants, desc=f'loading:{c}:{s}', leave=False):
                file_list = self._get_reading_filenames(year_from=year_from,
                                                        year_to=year_to,
                                                        since_date=since_date,
                                                        country_code=c,
                                                        pollutant=p,
                                                        station=s)

                if type(file_list) is dict:
                    e_msg = f"No files: {year_from}-{year_to}:{c}:{p}:{s} : {file_list.get('error', 'ERROR')}"
                    err_list.append(e_msg)
                    continue

                self._load_filelist(file_list, c, p, s, year_from, year_to, month)

        # display the errors
        for e in err_list:
            self.logger.info(e)

    def _load_by_countries(self, country_codes, pollutants, year_from, year_to, since_date, month):
        for c in tqdm(country_codes, desc='countries', leave=True):
            for p in tqdm(pollutants, desc=f'loading:{c}', leave=True):
                file_list = self._get_reading_filenames(year_from=year_from,
                                                        year_to=year_to,
                                                        since_date=since_date,
                                                        country_code=c,
                                                        pollutant=p,
                                                        station='')

                if type(file_list) is dict:
                    self.logger.info(file_list.get('error', 'ERROR'))
                    self.logger.info(f"No files found for {year_from}-{year_to} : {c}:{p}")
                    continue

                self._load_filelist(file_list, c, p, 'ALL STATIONS', year_from, year_to, month)

    def _load_filelist(self, file_list: list, c, p, s, year_from, year_to, month):
        """ Load data from a filelist """
        for f in tqdm(file_list, desc=f'files {c}:{p}:{s}:{year_from}-{year_to}', leave=False):
            if f == '':
                continue

            df = self._get_df_from_file(f)

            # if month was selected, limit table to the month
            if month != 0:
                from_date = datetime.datetime(year=year_from, month=month, day=1, tzinfo=pytz.timezone("CET"))
                to_date = datetime.datetime(year=year_from, month=month+1, day=1, tzinfo=pytz.timezone("CET"))
                df = df[(df['date_time'] >= from_date) & (df['date_time'] < to_date)]

            if df is not None:
                self._load_db_from_df(df)

    #######################
    # SUPPORT FUNCTIONS
    #######################
    def _load_db_from_df(self, df: pd.DataFrame):
        """
        Load readings data into database
        :param df: dataframe that includes the readings to load
        :return: None
        """
        # erase everything first
        # for station in ObservationStationReading.objects.all():
        #     station.delete()

        country_lookup = EUCountries.get_country_code_lookup()
        pollutant_lookup = Pollutant.get_observation_pollutants()

        r_list = []
        for row in tqdm(df.itertuples(), desc='loading rows', total=len(df), leave=False):

            # skip invalid readings
            if row.Validity != 1:
                continue

            country_code = country_lookup.get(row.Countrycode)
            if country_code is None:
                self.logger.debug(f"{row.Countrycode} skipped.  Not in NUTS regions.")
                continue

            pollutant = pollutant_lookup.get(row.AirPollutant)
            if pollutant is None:
                continue
            try:
                station = ObservationStation.objects.get(air_quality_station=row.AirQualityStation)
            except ObjectDoesNotExist as e:
                self.logger.debug(f"Station {row.AirQualityStation} not in master data. Skipping.")
                continue

            try:
                r_list.append(ObservationStationReading(
                                                    key=row.key,
                                                    date_time=row.date_time,
                                                    country_code=country_code,
                                                    air_quality_network=row.AirQualityNetwork,
                                                    air_quality_station=station,
                                                    pollutant=pollutant,
                                                    value=row.Concentration,
                                                    unit=row.UnitOfMeasurement,
                                                    validity=row.Validity,
                                                    verification=row.Verification))

            except Exception as e:
                continue

        ObservationStationReading.objects.bulk_create(r_list, ignore_conflicts=True)

    def _get_df_from_file(self, file_name: str) -> pd.DataFrame:

        def parse_date(s: pd.Series) -> datetime:
            tz = pytz.timezone("CET")
            ds = s.DatetimeEnd
            dt, tm, _ = ds.split(' ')
            yr, mon, day = dt.split('-')
            hr, minute, sec = tm.split(':')
            return datetime.datetime(int(yr), int(mon), int(day), int(hr), int(minute), int(sec), tzinfo=tz)

        def create_key(s: pd.Series) -> str:
            return s.date_time.strftime(f"%Y%m%d_%H_{s.AirQualityStation}_{s.AirPollutant}")

        try:
            df = pd.read_csv(file_name)
        except Exception as e:
            self.logger.info(file_name, e)
            # TODO: for SSL problems run "/Applications/Python\ 3.7/Install\ Certificates.command"
            return None

        # insert datetime and key fields
        df.insert(0, 'date_time', df.apply(parse_date, axis=1))
        df.insert(0, 'key', df.apply(create_key, axis=1))

        return df

    def _get_reading_filenames(self,
                               year_from: int,
                               year_to: int,
                               since_date: str,
                               country_code: str,
                               pollutant: str,
                               station: str):

        # get station readings
        url = f'https://fme.discomap.eea.europa.eu/fmedatastreaming/AirQualityDownload/AQData_Extract.fmw?CountryCode={country_code}&CityName=&Pollutant={pollutant}&Year_from={year_from}&Year_to={year_to}&Station={station}&Samplingpoint=&Source=All&Output=TEXT&UpdateDate={since_date}&TimeCoverage=Year'

        self.logger.debug("\tgetting request from url:")
        self.logger.debug("\t" + url)
        f = requests.get(url)
        self.logger.debug("\trequest complete.")

        if f.status_code != 200:
            return {'error': self._handle_web_error(f.status_code)}

        self.logger.debug("\tprocessing response ...")
        response = f.text
        response = response.split('\r')

        filelist = []
        for r in response:
            filelist.append("".join([x for x in r if x in string.printable]).strip())

        self.logger.debug("\tdone processing response.")

        filelist.remove('')

        return filelist

    @staticmethod
    def _handle_web_error(status_code) -> str:
        """
        Support function to handle web errors
        :param status_code - HTML status code returned from a request.
        """

        err_dict = {200: "200: OK",
                    400: "400: Parameter missing, parameter model is mandatory",
                    401: "401: Parameter token is invalid. Please specify &token=YOUR_KEY",
                    403: "403: Values of parameters are wrong.",
                    404: "404: Not Found",
                    503: "503: Server error. Try again later."}

        return err_dict.setdefault(status_code, f"{status_code}: unknown error status code.")
