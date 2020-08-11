"""
Author: Alan Martinson
Test for models_pollutants
"""
import pandas as pd
from django.test import TestCase
from airpollution.models import Measurement, Pollutant, Target
import json


class PollutantsMeasurementTest(TestCase):
    # print(">Testing PollutantsMeasurementTest")
    def setUp(self):
        Measurement.objects.create(
            measurement='m1',
            description='m1 reading'
            )

    def test_Measurement(self):
        theMeasurement = Measurement.objects.get(measurement='m1')
        self.assertEqual(theMeasurement.description, 'm1 reading')


class PollutantsPollutantTest(TestCase):
    # print(">Testing PollutantsPollutantTest")
    def setUp(self):
        Pollutant.objects.create(
            key='O3',
            copernicus_key='O3c',
            observation_key='O3o',
            eea_key='O3e'
            )

        Pollutant.objects.create(
            key='PM25',
            copernicus_key='PM25c',
            observation_key='PM25o',
            eea_key='PM25e'
            )

    def test_Pollutant(self):
        thePollutant = Pollutant.objects.get(key='O3')
        theKeys = Pollutant.get_keys()
        O3_keyc = Pollutant.get('O3c')
        O3_keyo = Pollutant.get('O3c')
        O3_keye = Pollutant.get('O3c')

        self.assertEqual(thePollutant.copernicus_key, 'O3c')
        self.assertEqual(thePollutant.observation_key, 'O3o')
        self.assertEqual(thePollutant.eea_key, 'O3e')

        # make sure there are two Pollutants
        self.assertEqual(theKeys, {'O3', 'PM25'})

        # make sure getting the Pollutant key works no matter which name is given
        self.assertEqual(O3_keyc, 'O3')
        self.assertEqual(O3_keyo, 'O3')
        self.assertEqual(O3_keye, 'O3')

        # get_eea_pollutants
        eeapollutants = Pollutant.get_eea_pollutants()
        theResults = ""
        for key in eeapollutants:
            theResults += key + "-" + eeapollutants[key].key + "-"
        self.assertEqual(theResults, "O3e-O3-PM25e-PM25-")

        # get_copernicus_pollutants
        copernicuspollutants = Pollutant.get_copernicus_pollutants()
        theResults = ""
        for key in copernicuspollutants:
            theResults += key + "-" + copernicuspollutants[key].key + "-"
        self.assertEqual(theResults, "O3c-O3-PM25c-PM25-")

        # get_observation_pollutants
        observationpollutants = Pollutant.get_observation_pollutants()
        theResults = ""
        for key in observationpollutants:
            theResults += key + "-" + observationpollutants[key].key + "-"
        self.assertEqual(theResults, "O3o-O3-PM25o-PM25-")


class PollutantsTargetTest(TestCase):
    # print(">Testing PollutantsTargetTest")
    def setUp(self):
        Measurement.objects.create(
            measurement='m1',
            description='m1 reading'
            )

        Pollutant.objects.create(
            key='O3',
            copernicus_key='O3c',
            observation_key='O3o',
            eea_key='O3e'
            )

        theMeasurement = Measurement.objects.get(measurement='m1')
        thePollutant = Pollutant.objects.get(key='O3')

        Target.objects.create(
            unit='unit1',
            value=3.14,
            count_limit=10,
            measurement=theMeasurement,
            pollutant=thePollutant
            )

    def test_Target(self):
        theData = Target.objects.get(unit='unit1')
        self.assertEqual(theData.value, 3.14)
        self.assertEqual(theData.count_limit, 10)

        # get_all_targets
        allTargets = Pollutant.get_all_targets(years=['2020'], country_codes=['AT'])
        x = allTargets.get('AT').get('2020').get('O3').get('m1')
        self.assertEqual(x.get('unit'), 'unit1')
        self.assertEqual(x.get('value'), 3.14)
        self.assertEqual(x.get('count_limit'), 10)

        # get_targets_df
        df = Pollutant.get_targets_df()
        self.assertEqual(type(df), pd.DataFrame)

        # get_pollutant_dayavg_by_station_df
        df = Pollutant.get_pollutant_dayavg_by_station_df(date_from='2020-01-01', date_to='2020-12-31', pollutant='O3')
        self.assertEqual(type(df), pd.DataFrame)
