"""
Author: Hemant Bajpai
Test for EuroStat Data Model
"""
from django.test import TestCase
from airpollution.models import EurostatDataModel

class EurostatModelTests(TestCase):
    def setUp(self):
        EurostatDataModel.objects.create(
            year=2020,
            population=200,
            nutsRegionStr='AL01')

    def test_eurostatdatamodel_get_population_info(self):
        """Test EurostatDataModel.get_population_info"""
        eurostatData = EurostatDataModel.objects.get(year=2020)
        self.assertEqual(eurostatData.year, 2020)
        self.assertEqual(eurostatData.population, 200)
        self.assertEqual(eurostatData.nutsRegionStr, 'AL01')
        rv = EurostatDataModel.get_population_info('AL01', 2020)
        self.assertEqual(rv['AL01'], 200)