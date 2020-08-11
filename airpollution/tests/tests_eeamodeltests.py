"""
Author: Hemant Bajpai
Test for EEA Data Model
"""
from django.test import TestCase
from airpollution.models import EEADataModel

class EEAModelTests(TestCase):
    def setUp(self):
        EEADataModel.objects.create(
            year=2020,
            pollutant_name='SOx',
            country='EU28',
            sector_group='TOTAL_EMISSION',
            emissions=100)

    def test_eeadatamodel_get_sectors_info(self):
        """Test EEADataModel.get_sectors_info"""
        eeaData = EEADataModel.objects.get(pollutant_name='SOx')
        self.assertEqual(eeaData.year, 2020)
        self.assertEqual(eeaData.pollutant_name, 'SOx')
        self.assertEqual(eeaData.country, 'EU28')
        self.assertEqual(eeaData.emissions, 100)
        rv = EEADataModel.get_sectors_info(2020)
        self.assertEqual(rv['EU28'][2020]['SOx']['TOTAL_EMISSION'], 100)

