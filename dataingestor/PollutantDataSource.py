"""
Author: Mark McDonald
Pollutant data source.  Includes a dictionary of pollutants including mappings to pollutant
name across multiple platforms as well as the target values for pollutants and methods
used to calculate target attainment.

The load_data method contains the specific data associated with the pollutants.  Changes
or additions can be added to that section.

If a new measurement is needed, a new Measurements sub class should be added.

"""
import logging

from airpollution.models import Target, Measurement, Pollutant
from dataingestor.DataSource import DataSource


class PollutantDataSource(DataSource):

    def __init__(self, logger: logging.Logger):
        DataSource.__init__(self, "Pollutants", "Dictionary of Pollutants, mappings and measurements")
        self.logger = logger

    def load_data(self, **kwargs) -> None:

        # erase everything first
        for t in Target.objects.all():
            t.delete()
        for m in Measurement.objects.all():
            m.delete()
        for p in Pollutant.objects.all():
            p.delete()

        # CREATE MEASUREMENTS
        msmt_year = Measurement.objects.create(
            measurement="calendar_year",
            description="measured as the average for the year")
        msmt_year.save()

        msmt_day = Measurement.objects.create(
            measurement="day",
            description="measured as the number of times the daily average exceeds the value")
        msmt_day.save()

        msmt_hour = Measurement.objects.create(
            measurement="hour",
            description="measured as the number of hours a measure is exceeded in a year")
        msmt_hour.save()

        msmt_max8 = Measurement.objects.create(
            measurement="max_8hour_mean",
            description="measured as the number of days where the limit is exceeded at least once in the day")
        msmt_max8.save()

        # PM25
        pol = Pollutant.objects.create(
            key='PM25',
            copernicus_key='pm2p5_conc',
            observation_key='PM2.5',
            eea_key='PM2.5')
        pol.save()

        tar = Target.objects.create(
            pollutant=pol,
            measurement=msmt_year,
            unit='ug/m3',
            value=25,
            count_limit=None)
        tar.save()

        # PM10
        pol = Pollutant.objects.create(
            key='PM10',
            copernicus_key='pm10_conc',
            observation_key='PM10',
            eea_key='PM10')
        pol.save()
        tar = Target.objects.create(
            pollutant=pol,
            measurement=msmt_day,
            unit='ug/m3',
            value=50,
            count_limit=35)
        tar.save()
        tar = Target.objects.create(
            pollutant=pol,
            measurement=msmt_year,
            unit='ug/m3',
            value=40,
            count_limit=None)
        tar.save()

        # O3
        pol = Pollutant.objects.create(
            key='O3',
            copernicus_key='o3_conc',
            observation_key='O3')
        pol.save()
        tar = Target.objects.create(
            pollutant=pol,
            measurement=msmt_max8,
            unit='ug/m3',
            value=120,
            count_limit=25)
        tar.save()

        # NO2
        pol = Pollutant.objects.create(
            key='NO2',
            copernicus_key='no2_conc',
            observation_key='NO2',
            eea_key='NO2')
        pol.save()
        tar = Target.objects.create(
            pollutant=pol,
            measurement=msmt_hour,
            unit='ug/m3',
            value=200,
            count_limit=18)
        tar.save()

        tar = Target.objects.create(
            pollutant=pol,
            measurement=msmt_year,
            unit='ug/m3',
            value=40,
            count_limit=None)
        tar.save()

        # NOx
        pol = Pollutant.objects.create(
            key='NOx',
            eea_key='NOx')
        pol.save()

        # CO
        pol = Pollutant.objects.create(
            key='CO',
            copernicus_key='co_conc',
            observation_key='CO',
            eea_key='CO')
        pol.save()

        # SO2
        pol = Pollutant.objects.create(
            key='SO2',
            copernicus_key='so2_conc',
            observation_key='SO2')
        pol.save()

        # SOx
        pol = Pollutant.objects.create(
            key='SOx',
            eea_key='SOx')
        pol.save()

        # PANS
        pol = Pollutant.objects.create(
            key='PANS',
            copernicus_key='pans_conc',
            observation_key=None)
        pol.save()

        # NMVOC
        pol = Pollutant.objects.create(
            key='NMVOC',
            copernicus_key='nmvoc_conc',
            observation_key=None,
            eea_key='NMVOC')
        pol.save()

        # NO
        pol = Pollutant.objects.create(
            key='NO',
            copernicus_key='no_conc',
            observation_key='NO')
        pol.save()

        # NH3
        pol = Pollutant.objects.create(
            key='NH3',
            copernicus_key='nh3_conc',
            observation_key=None,
            eea_key='NH3')
        pol.save()

        # BIRCHPOLLEN
        pol = Pollutant.objects.create(
            key='BIRCHPOLLEN',
            copernicus_key='bpg_conc',
            observation_key=None)
        pol.save()

        # OLIVEPOLLEN
        pol = Pollutant.objects.create(
            key='OLIVEPOLLEN',
            copernicus_key='opg_conc',
            observation_key=None)
        pol.save()

        # GRASSPOLLEN
        pol = Pollutant.objects.create(
            key='GRASSPOLLEN',
            copernicus_key='gpg_conc',
            observation_key=None)
        pol.save()

        # RAGWEEDPOLLEN
        pol = Pollutant.objects.create(
            key='RAGWEEDPOLLEN',
            copernicus_key='rwpg_conc',
            observation_key=None)
        pol.save()

        # # Pb
        # pol = Pollutant.objects.create(
        #     key='PB',
        #     copernicus_key=None,
        #     observation_key='Pb',
        #     eea_key=None)
        # pol.save()

        # Ni
        # pol = Pollutant.objects.create(
        #     key='NI',
        #     copernicus_key=None,
        #     observation_key='Ni',
        #     eea_key=None)
        # pol.save()

        # Cr
        # pol = Pollutant.objects.create(
        #     key='CR',
        #     copernicus_key=None,
        #     observation_key='Cr',
        #     eea_key=None)
        # pol.save()

        # Cd
        # pol = Pollutant.objects.create(
        #     key='CD',
        #     copernicus_key=None,
        #     observation_key='Cd',
        #     eea_key=None)
        # pol.save()

        # Cu
        # pol = Pollutant.objects.create(
        #     key='CU',
        #     copernicus_key=None,
        #     observation_key='Cu',
        #     eea_key=None)
        # pol.save()

        # As
        # pol = Pollutant.objects.create(
        #     key='AS',
        #     copernicus_key=None,
        #     observation_key='As',
        #     eea_key=None)
        # pol.save()

        # NOx
        # pol = Pollutant.objects.create(
        #     key='NOX',
        #     copernicus_key=None,
        #     observation_key='NOx',
        #     eea_key=None)
        # pol.save()

        # SOx
        # pol = Pollutant.objects.create(
        #     key='SOX',
        #     copernicus_key=None,
        #     observation_key='SOx',
        #     eea_key=None)
        # pol.save()

        self.logger.info("Loaded pollutants.")

    def load_dummy_data(self):
        pass
