"""
Author: Mark McDonald
This model holds nuts regions and shape geometry
"""
import logging
import shapely.wkt
from shapely.geometry import Point

from django.db import models

import geopandas as gpd

# Default NUTS version - 4-digit integer of year version published
CURRENT_NUTS_VERSION = 2016
EU_ISOCODES = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI',
               'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU',
               'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'UK']


class NutsRegions(models.Model):
    """
    Hold nuts regional information including geometry
    """
    key = models.CharField(max_length=32, primary_key=True)
    year = models.CharField(max_length=4, db_index=True)
    id = models.CharField(max_length=8, db_index=True)
    LEVL_CODE = models.IntegerField(blank=True, db_index=True)
    NUTS_ID = models.CharField(max_length=16, db_index=True)
    CNTR_CODE = models.CharField(max_length=64, db_index=True)
    NUTS_NAME = models.CharField(max_length=128, db_index=True)
    FID = models.CharField(max_length=16, db_index=True)
    EU_MEMBER = models.BooleanField()
    geometry = models.CharField(max_length=4194304)

    def __str__(self):
        return self.NUTS_ID

    @staticmethod
    def get_nuts_region_boundaries(nuts_level: list = None, country_codes: list = None,
                                   year: int = CURRENT_NUTS_VERSION) -> dict:
        """
        Return the basic regional information for NUTS regions.
        :param nuts_level: Nuts level for which to return data.  If None, all are returned.
        :param country_codes: List of country code for which boundaries are returned.  If None, all EU countries are returned.
        :param year: The year of the NUTS version..  Defaults to the current version.
        :return: A dictionary with the shape objects for each NUTS region.
        """

        def _create_level_dict(level_qs, country_list: list) -> dict:
            rv = {}
            for r in level_qs:
                if r.CNTR_CODE in country_list:
                    rv.update({r.NUTS_ID: {'name': r.NUTS_NAME,
                                           'country_code': r.CNTR_CODE,
                                           'geography': r.geometry}})
            return rv

        if nuts_level is None:
            levels_list = [0, 1, 2, 3]
        else:
            levels_list = [nuts_level]

        if country_codes is None:
            country_codes = EU_ISOCODES
        else:
            country_codes = [c.upper() for c in country_codes]

        rv_dict = {}
        for level in levels_list:
            qs = NutsRegions.objects.filter(LEVL_CODE=level, year=year)
            rv_dict.update({level: _create_level_dict(qs, country_codes)})

        return rv_dict

    @staticmethod
    def get_nuts_regions(nuts_level: int = None, year: int = CURRENT_NUTS_VERSION) -> dict:
        """
        Return the basic regional information for NUTS regions.
        :param nuts_level: Nuts level for which to return data
        :param year: The NUTS year
        :return: dictionary of data
        """

        def _create_level_dict(level_qs) -> dict:
            rv = {}
            for r in level_qs:
                rv.update({r.NUTS_ID: {'name': r.NUTS_NAME, 'country_code': r.CNTR_CODE}})
            return rv

        if nuts_level is None:
            levels_list = [0, 1, 2, 3]
        else:
            levels_list = [nuts_level]

        rv_dict = {}
        for level in levels_list:
            qs = NutsRegions.objects.filter(LEVL_CODE=level, year=year)
            rv_dict.update({level: _create_level_dict(qs)})

        return rv_dict

    @staticmethod
    def get_country_code_lookup() -> dict:
        country_lookup = {}
        for c in EU_ISOCODES:
            try:
                country_lookup.update({c: NutsRegions.objects.get(CNTR_CODE=c, LEVL_CODE=0)})
            except Exception as e:
                logging.debug(f"'{c}' skipped.  Not in NUTS regions.")

        return country_lookup

    @staticmethod
    def get_nuts_geoframe(nuts_version: int = 2016, crs: int = 4326, nuts_level: int = None) -> gpd.GeoDataFrame:
        """
        Return the NUTS regions data as a Pandas GeoDataFrame.
        :param nuts_level: Optional.  If None, all are returned.
        :param nuts_version: Optional. Set to 2016.
        :param crs: Optional. Default set to 4326.
        :return: GeoPandas DataFrame with NUTS regions
        """

        gdf = gpd.GeoDataFrame()

        if nuts_level is not None:
            qs = NutsRegions.objects.filter(LEVL_CODE=nuts_level, year=nuts_version)
        else:
            qs = NutsRegions.objects.filter(year=nuts_version)

        for record in qs:
            d = {'key': record.key,
                 'year': record.year,
                 'id': record.id,
                 'LEVL_CODE': record.LEVL_CODE,
                 'NUTS_ID': record.NUTS_ID,
                 'CNTR_CODE': record.CNTR_CODE,
                 'NUTS_NAME': record.NUTS_NAME,
                 'FID': record.FID,
                 'db_record': record,
                 'geometry': gpd.GeoSeries(shapely.wkt.loads(record.geometry))}  # record.geometry}

            gdf = gdf.append(gpd.GeoDataFrame(d), ignore_index=True)

        gdf.crs = crs  # set the projection

        return gdf

    @staticmethod
    def get_nuts_record(lat, lon, crs: int, nuts_level: int, nuts_version: int = 2016):
        """
        Returns a single NUTS record based on lat lon and nuts_level
        :param lat: Latitude of the point
        :param lon: Longitude of the point
        :param crs: CRS of the point
        :param nuts_level: Required. Level of record to return.
        :param nuts_version: The NUTS version/year as 4-digit year YYYY. Optional. Defaults to 2016.

        :return: The results records from the dataset where the lat/lon point is in.
        """

        gdf = NutsRegions.get_nuts_geoframe(nuts_level=nuts_level)

        point = gpd.GeoSeries(Point(lon, lat), crs=crs).to_crs(gdf.crs)[0]

        try:
            nuts_key = gdf[(gdf.contains(point)) & (gdf.LEVL_CODE == nuts_level)].iloc[0].key
        except (AttributeError, Exception) as e:
            err = f"{e} : lat:{lat}  lon:{lon}  nuts_level:{nuts_level}  year:{nuts_version}  crs:{crs}"
            logging.info(err)
            return None

        return NutsRegions.objects.get(pk=nuts_key)


class EUCountries(models.Model):
    key = models.CharField(max_length=4, primary_key=True)
    nuts_region = models.ForeignKey(NutsRegions, on_delete=models.DO_NOTHING, null=True, related_name="EU_countries",
                                    db_index=True)

    def __str__(self):
        return self.key

    @staticmethod
    def get_country_code_lookup() -> dict:

        eu_countries = EUCountries.objects.all()

        country_lookup = {}
        for c in eu_countries:
            try:
                country_lookup.update({str(c.key): c})
            except Exception as e:
                logging.debug(f"'{c}' skipped.  Not an EU country.")

        return country_lookup



