import os
from unittest.mock import patch

import netCDF4
from django.test import TestCase

from airpollution.models import SatelliteImageFiles, Pollutant
from eugreendeal.settings import BASE_DIR


class SatelliteImageFilesTestCase(TestCase):
    def setUp(self):
        pollutant = Pollutant.objects.create(
            key='O3',
            copernicus_key='o3_conc',
            observation_key='O3',
            eea_key='O3')
        SatelliteImageFiles.objects.create(key='key1', pollutant=pollutant, year=2016, month=5, day=2,
                                           category='ANALYSIS', file_path='/somefilepath', bbox_minlon=0.0,
                                           bbox_minlat=0.0, bbox_maxlon=0.0, bbox_maxlat=0.0, shape="2 4",
                                           image="1.3150195 1.310131 1.2987623 1.294859 1.3038024 1.3086151 1.3102827 1.3053561")
        SatelliteImageFiles.objects.create(key='key2', pollutant=pollutant, year=2017, month=5, day=2,
                                           category='ANALYSIS', file_path='/somefilepath', bbox_minlon=0.0,
                                           bbox_minlat=0.0, bbox_maxlon=0.0, bbox_maxlat=0.0, shape="2 4",
                                           image="1.3150195 1.310131 1.2987623 1.294859 1.3038024 1.3086151 1.3102827 1.3053561")

    def test_satelliteimagefiles_get_sat_image(self):
        """Test SatelliteImageFiles.get_sat_image"""
        pollutant = Pollutant.objects.get(pk='O3')
        self.assertEqual(pollutant.key, 'O3')
        self.assertEqual(SatelliteImageFiles.objects.filter(pollutant=pollutant).all()[0].file_path, '/somefilepath')
        test_data_filepath = os.path.join(BASE_DIR, 'airpollution', 'tests', 'test_data', 'testout.nc')
        ncout = netCDF4.Dataset(test_data_filepath)
        self.assertEqual(ncout['o3_conc'][12, 0, :][0], 0)
        with patch('netCDF4.Dataset') as mock:
            mock.return_value = ncout
            image = SatelliteImageFiles.get_sat_image('O3', 2016, 5, 2)
            self.assertEqual(image[0][0], 1.3150195)
            mock.assert_not_called()

