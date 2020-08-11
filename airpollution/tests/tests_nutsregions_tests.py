"""
Author: Alan Martinson
Test for nuts_regions
"""
from django.test import TestCase
from airpollution.models import NutsRegions, EUCountries

class NutsRegionsTest(TestCase):
    def setUp(self):
        NutsRegions.objects.create(
            key='key1',
            year='2020',
            NUTS_ID='ID1',
            LEVL_CODE=1,
            EU_MEMBER=1
            )

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

        EUCountries.objects.create(
            key='AT',
            nuts_region=NutsRegions.objects.get(CNTR_CODE='AT', LEVL_CODE='0')
        )

    def test_Nutsregion(self):
        nutsData = NutsRegions.objects.get(key='key1')
        self.assertEqual(nutsData.year, '2020')
        self.assertEqual(nutsData.NUTS_ID, 'ID1')
        self.assertEqual(nutsData.LEVL_CODE, 1)

        EUcountry_lookup = EUCountries.get_country_code_lookup()
        EUcountry_code = EUcountry_lookup.get('AT')
        self.assertEqual(EUcountry_code.key, 'AT')

        NUTScountry_lookup = NutsRegions.get_country_code_lookup()
        NUTScountry_code = NUTScountry_lookup.get('AT')
        self.assertEqual(NUTScountry_code.NUTS_ID, 'AT')