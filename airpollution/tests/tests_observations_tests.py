import logging
import datetime
import pytz
from dateutil.tz import *

import pandas as pd
import geopandas as gpd
from django.test import TestCase
from django.db.models import Avg
from airpollution.models import Pollutant, ObservationStation, ObservationStationReading, NutsRegions, EUCountries


class ObservationStationTest(TestCase):

    def setUp(self):
        NutsRegions.objects.create(
            key='0',
            year='2016',
            id='0',
            LEVL_CODE='0',
            NUTS_ID='AT',
            CNTR_CODE='AT',
            NUTS_NAME='AT',
            FID='0',
            EU_MEMBER=True,
            geometry='none'
        )

        NutsRegions.objects.create(
            key='1',
            year='2016',
            id='1',
            LEVL_CODE='1',
            NUTS_ID='AT1',
            CNTR_CODE='AT',
            NUTS_NAME='AT 1',
            FID='1',
            EU_MEMBER=True,
            geometry='none'
        )

        NutsRegions.objects.create(
            key='2',
            year='2016',
            id='2',
            LEVL_CODE='2',
            NUTS_ID='AT11',
            CNTR_CODE='AT',
            NUTS_NAME='AT 11',
            FID='2',
            EU_MEMBER=True,
            geometry='none'
        )

        NutsRegions.objects.create(
            key='3',
            year='2016',
            id='3',
            LEVL_CODE='3',
            NUTS_ID='AT111',
            CNTR_CODE='AT',
            NUTS_NAME='AT 111',
            FID='3',
            EU_MEMBER=True,
            geometry='none'
        )

        EUCountries.objects.create(
            key='AT',
            nuts_region=NutsRegions.objects.get(CNTR_CODE='AT', LEVL_CODE='0')
        )

        ObservationStation.objects.create(
            air_quality_station='1',
            country_code=EUCountries.objects.get(pk='AT'),
            air_quality_network='aq_network',
            air_quality_station_eoicode='aq_eoicode',
            air_quality_station_natcode='aq_natcode',
            projection='aq_projection',
            longitude=123.123,
            latitude=123.123,
            altitude=123.123,
            nuts_1=NutsRegions.objects.get(NUTS_ID='AT1'),
            nuts_2=NutsRegions.objects.get(NUTS_ID='AT11'),
            nuts_3=NutsRegions.objects.get(NUTS_ID='AT111'),
            air_quality_station_area='aq_station_area'
        )

        Pollutant.objects.create(
            key='O3',
            copernicus_key='O3c',
            observation_key='O3o',
            eea_key='O3e'
        )

        ObservationStationReading.objects.create(
            key='1',
            date_time=datetime.datetime(year=2020, month=4, day=15, tzinfo=tzlocal()),
            country_code=EUCountries.objects.get(pk='AT'),
            air_quality_network='aq_network',
            air_quality_station=ObservationStation.objects.get(pk='1'),
            pollutant=Pollutant.objects.get(pk='O3'),
            value=123.123,
            unit='unit',
            validity=1,
            verification=1
        )

    def test_get_country_code(self):
        station = ObservationStation.objects.get(air_quality_station='1')
        country_code = ObservationStation.get_country_code(station.air_quality_station)
        self.assertEqual(country_code.key, 'AT')

    def test_get_stratified_stations(self):
        stations_list = ObservationStation.get_stratified_stations()
        self.assertEqual(stations_list, ['1'])

    def test_daily(self):
        logger = logging.Logger(name='tester')
        test_val = ObservationStationReading.daily(start_date='2020-01-01', end_date='2020-12-31', logger=logger)
        test_dict = list(test_val.values())[0].values()
        test_list = list(test_dict)[0].get('O3').values()
        self.assertEqual(list(test_list), [123.123, 123.123, 0, 0])

    def test_annual(self):
        logger = logging.Logger(name='tester')
        test_dict = ObservationStationReading.annual(countries=['AT'], years=[2020], pollutants=['O3'], logger=logger)
        self.assertEqual(test_dict.get('AT').get(2020).get('O3'), 123.123)
