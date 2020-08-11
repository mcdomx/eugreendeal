"""
Author: Mark McDonald
This class will handle loading nuts regional data
"""
import os
import logging

from tqdm import tqdm
import geopandas as gpd
import pandas as pd

from airpollution.models.models_nuts import NutsRegions, EU_ISOCODES, EUCountries
from dataingestor.DataSource import DataSource
from eugreendeal.settings import MEDIA_ROOT

DATA_DIR = os.path.join(MEDIA_ROOT, 'media', 'mapdata', 'ref-nuts-2016-60m')


class NutsDataSource(DataSource):

    def __init__(self, name: str, logger: logging.Logger, description: str = None):
        DataSource.__init__(self, name, description)
        self.logger = logger

    def set_token(self) -> str:
        pass

    def load_data(self, year: str = 2016, crs: int = 4326, nuts_level: int = None):

        self.logger.info("Loading NUTS maps data .. ")

        # erase everything first
        # for region in NutsRegions.objects.all():
        #     region.delete()

        for nuts_level in [0, 1, 2, 3]:
            self.logger.info(f"Loading NUTS level {nuts_level}")
            # get a dataframe from a file
            df = self._get_df_from_file(year=year, crs=crs, nuts_level=nuts_level)

            # load_db from the df
            self._load_data_from_df(df)

        # Load EU countries
        self._load_EU_countries()

        self.logger.info("Done Loading NUTS data.. ")

    def load_dummy_data(self):
        pass

    def get_data(self, **kwargs):
        pass

    #######################
    # SUPPORT FUNCTIONS
    #######################
    def _load_EU_countries(self):
        country_code_lookup = NutsRegions.get_country_code_lookup()
        for k, v in country_code_lookup.items():
            try:
                record = EUCountries.objects.create(key=k,
                                                    nuts_region=v)
                record.save()
            except Exception as e:
                self.logger.debug(f"Item not loaded. '{k}' {e}")

    def _load_data_from_df(self, df: gpd.GeoDataFrame) -> None:
        records = []
        loaded = skipped = 0
        for index, row in tqdm(df.iterrows(), desc='loading regions'):

            try:
                record = NutsRegions.objects.create(key=row.key,
                                                    year=row.year,
                                                    id=row.id,
                                                    LEVL_CODE=row.LEVL_CODE,
                                                    NUTS_ID=row.NUTS_ID,
                                                    CNTR_CODE=row.CNTR_CODE,
                                                    NUTS_NAME=row.NUTS_NAME,
                                                    FID=row.FID,
                                                    EU_MEMBER=True if row.CNTR_CODE in EU_ISOCODES else False,
                                                    geometry=row.geometry.to_wkt())

                loaded += 1
                records.append(record)
                if loaded % 10000 == 0:
                    NutsRegions.objects.bulk_create(records, ignore_conflicts=True)
                    records.clear()

            except Exception as e:
                self.logger.debug(e)
                self.logger.debug("Item skipped and not loaded. Item not loaded listed below:")
                skipped += 1

                for k, v in row.iteritems():
                    self.logger.debug(f"\t{k}: {v}")

        if len(records) > 0:
            NutsRegions.objects.bulk_create(records, ignore_conflicts=True)

        records.clear()

        self.logger.debug(f"Loaded {loaded} observations. Skipped {skipped}")

    def _get_df_from_file(self, year: str, crs: int, nuts_level: int) -> gpd.GeoDataFrame:
        """
        Get a GeoPandas dataframe based on a json file.
        :param crs: The crs to use #[4326, 3857, 3035]
        :param nuts_level: The nuts level  #[None, 0, 1 ,2, 3]
        :return: GeoPandas dataframe
        """

        def _create_key(s: pd.Series) -> str:
            k = f'{s.year}_{s.LEVL_CODE}_{s.id}'
            return k

        if nuts_level is None:
            filepath = os.path.join(DATA_DIR, f'NUTS_RG_60M_{year}_{crs}.geojson')
        else:
            filepath = os.path.join(DATA_DIR, f'NUTS_RG_60M_{year}_{crs}_LEVL_{nuts_level}.geojson')

        df = gpd.read_file(filepath)
        df['year'] = year
        df['key'] = df.apply(_create_key, axis=1)

        df.crs = crs
        df = self._crop_map(df)

        return df

    def _crop_map(self, df: gpd.GeoDataFrame, minx=-24.95, miny=30.05, maxx=44.95, maxy=71.95) -> gpd.GeoDataFrame:
        """
        Will crop a geopandas dataframe to the area defined by the x and y boundaries provided.
        :param df:
        :param minx: Minimum longitude
        :param miny: Minimum latitude
        :param maxx: Maximum longitude
        :param maxy: Maximum latitude
        :return: A cropped Geopandas dataframe
        """
        return df.cx[minx:maxx, miny:maxy]
