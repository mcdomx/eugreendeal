import os
import pandas as pd
import geopandas as gpd
import numpy as np
from tqdm import tqdm
import logging
import requests

from airpollution.models.models_observations import ObservationStation
from airpollution.models.models_nuts import NutsRegions, EUCountries, CURRENT_NUTS_VERSION
from eugreendeal.settings import MEDIA_ROOT
from dataingestor.DataSource import DataSource


class EEAStationDataSource(DataSource):

    def __init__(self, name: str, logger: logging.Logger, description: str = None):
        DataSource.__init__(self, name, description)
        self.logger = logger

    def load_data(self, **kwargs) -> str:
        if not kwargs.get('url'):
            self.logger.error("url argument not provided.")
            return ""

        if not kwargs.get('target_dir'):
            self.logger.error("target_dir argument not provided.")
            return ""

        url = kwargs.get('url')
        target_dir = kwargs.get('target_dir')

        if kwargs.get('load_from_file'):
            fpath = os.path.join(target_dir, url.split('/')[-1])
        else:
            # download the latest meta-data for observation stations
            fpath = self._download_stations_metadata(url, target_dir)

        # create a df from the downloaded file
        df = self._get_station_df(filename=fpath)
        self._load_db_from_df(df)

    def load_dummy_data(self):
        pass

    #######################
    # SUPPORT FUNCTIONS
    #######################
    def _download_stations_metadata(self, url: str, target_dir: str) -> str:
        """
        Download the latest metadata for observation stations
        :param url: optional.  Will default to the standard location.
        :param target_dir: optional.  Will default to the application's defaulted location
        :return: The full path of the saved file
        """

        self.logger.info("Downloading station meta data ...")

        if not url:
            url = "http://discomap.eea.europa.eu/map/fme/metadata/PanEuropean_metadata.csv"

        if not target_dir:
            target_dir = os.path.join(MEDIA_ROOT, 'observation_data')

        self.logger.debug(f"Getting request from eea ... ")
        r = requests.get(url)
        self.logger.debug(f"Request returned with status {r.status_code}")

        if r.status_code != 200:
            self.logger.error(f"{_handle_web_error(r.status_code)}")
            self.logger.error(url)
            return None
        else:
            try:
                # determine the filename
                fname = url.split('/')[-1]

                # create a full path to save file to
                fpath = os.path.join(target_dir, fname)

                with open(fpath, "wb") as f:
                    self.logger.debug("Saving file ...")
                    f.write(r.content)
                    self.logger.debug("File saved!")

                self.logger.info("Done downloading station meta data ...")
                return fpath

            except Exception as e:
                self.logger.error(f"Error saving file. {e}")
                self.logger.error(f"\t{fpath}")
                return None

    def _get_station_df(self, filename: str) -> gpd.GeoDataFrame:
        """
        Returns a dataframe with meta-data for pollutant observation stations
        :param filename: filename of the csv file.  File must be located in the media/observation_data directory
        :return: GeoPandas Dataframe with the meta-data fields to be loaded into the db.
        """
        def strip_station(s: pd.Series) -> str:
            return s.AirQualityStation.strip()

        station_file = os.path.join(MEDIA_ROOT, 'observation_data', filename)
        station_metadata = pd.read_csv(station_file, sep='\t')

        # Each station is listed for each pollutant that it can measure.
        # We will drop this information and the drop duplicate items in the list.
        drop_cols = ['AirPollutantCode', 'SamplingProces', 'ObservationDateBegin', 'ObservationDateEnd',
                     'MeasurementEquipment', 'EquivalenceDemonstrated', 'BuildingDistance', 'InletHeight',
                     'KerbDistance', 'SamplingPoint', 'Sample', 'MeasurementType', 'AirQualityStationType']
        station_metadata.drop(columns=drop_cols, inplace=True)

        # now, we can drop the duplicates
        station_metadata.drop_duplicates(inplace=True)
        station_metadata.reset_index(inplace=True, drop=True)

        # extract the projection
        crs = np.unique(station_metadata.Projection)[0]

        # create GeoDataFrame based on crs, lon and lat
        station_metadata = gpd.GeoDataFrame(station_metadata,
                                            crs=crs,
                                            geometry=gpd.points_from_xy(station_metadata.Longitude,
                                                                        station_metadata.Latitude))

        # change the projection - only changes point locations - not lat and lon
        station_metadata = station_metadata.to_crs("EPSG:4326")

        # clean station names
        station_metadata['AirQualityStation'] = station_metadata.apply(strip_station, axis=1)

        return station_metadata

    @staticmethod
    def _add_nuts_regions_to_df(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Add NUTS region objects to the stations dataframe
        :param gdf: The stations geopands dataframe created from _get_station_df()
        :return: The same dataframe with the addition of the nuts regions
        """

        # get a NUTS geoframe for local speed
        nuts_gdf = NutsRegions.get_nuts_geoframe(nuts_version=CURRENT_NUTS_VERSION)

        def add_nuts(s: gpd.GeoSeries) -> gpd.GeoSeries:
            rv = nuts_gdf[nuts_gdf.contains(s.geometry)][['LEVL_CODE', 'db_record']]
            rv.set_index('LEVL_CODE', drop=True, inplace=True)
            rv.rename(index={0: 'NUTS_0', 1: 'NUTS_1', 2: 'NUTS_2', 3: 'NUTS_3'}, inplace=True)
            return s.append(rv.T.iloc[0])

        # make sure the nuts_df and the stations_df have the same crs
        gdf = gdf.to_crs(nuts_gdf.crs)

        # apply the nuts columns based on location
        return gdf.apply(add_nuts, axis=1)

    def _load_db_from_df(self, stations_gdf: gpd.GeoDataFrame) -> str:
        """
        Load the DB based on a data frame.

        :return: None
        """
        # erase everything first
        # self.logger.info("Deleting old entries ...")
        # for station in ObservationStation.objects.all():
        #     station.delete()
        # self.logger.info("Deletions Completed.")

        # make a lookup for country_code
        country_lookup = EUCountries.get_country_code_lookup()

        stations_gdf = EEAStationDataSource._add_nuts_regions_to_df(stations_gdf)

        self.logger.info(f"Loading {len(stations_gdf)} stations to local data base ...")

        count = 0
        r_list = []
        for row in tqdm(stations_gdf.itertuples(), desc='loading stations'):

            country_code = country_lookup.get(row.Countrycode)
            if country_code is None:
                self.logger.debug(f"{row.Countrycode} skipped.  Not in NUTS regions.")
                continue

            try:
                r_list.append(ObservationStation.objects.create(
                    air_quality_station=row.AirQualityStation,
                    country_code=country_code,
                    air_quality_network=row.AirQualityNetwork,
                    air_quality_station_eoicode=row.AirQualityStationEoICode,
                    air_quality_station_natcode=row.AirQualityStationNatCode,
                    projection=row.Projection,
                    longitude=row.Longitude,
                    latitude=row.Latitude,
                    altitude=row.Altitude,
                    # nuts_0=row.NUTS_0,
                    nuts_1=row.NUTS_1,
                    nuts_2=row.NUTS_2,
                    nuts_3=row.NUTS_3,
                    air_quality_station_area=row.AirQualityStationArea))

                # record.save()
                count += 1

                if count % 10000 == 0:
                    ObservationStation.objects.bulk_create(r_list, ignore_conflicts=True)
                    r_list.clear()

            except Exception as e:
                # take no action. duplicates are expected as new files are loaded.
                # print(e)
                # print(row)
                continue

        if len(r_list) > 0:
            ObservationStation.objects.bulk_create(r_list, ignore_conflicts=True)
            r_list.clear()

        self.logger.info(f"Done downloading station meta data.  Loaded {count} stations.")

        return f"Loaded {count} stations."

    @staticmethod
    def get_all() -> dict:
        rs = ObservationStation.objects.values()
        return rs
        # rv = {}
        # for r in rs:
        #     rv.update({r.air_quality_station: {
        #         'country_code': r.country_code,
        #         'air_quality_network': r.air_quality_network,
        #         'air_quality_station_area': r.air_quality_station_area,
        #         'air_quality_station_eoicode': r.air_quality_station_eoicode,
        #         'air_quality_station_natcode': r.air_quality_station_natcode,
        #         'projection': r.projection,
        #         'longitude': r.longitude,
        #         'latitude': r.latitude,
        #         'altitude': r.altitude,
        #         'nuts_1': r.nuts_1_id,
        #         'nuts_2': r.nuts_2_id,
        #         'nuts_3': r.nuts_3_id,
        #     }})


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