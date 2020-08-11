"""
Author: Mark McDonald
This model holds pollutants including the reference keys to various datasource
and the pollutant targets
"""
import logging
import datetime
import pytz
import pandas as pd

from django.db import models
from django.db.models import Q, Avg
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from airpollution.models.models_nuts import EU_ISOCODES


class Measurement(models.Model):
    """
    """
    measurement = models.CharField(primary_key=True, max_length=16)
    description = models.CharField(max_length=256)

    def __str__(self):
        return f"{self.measurement}"


class Pollutant(models.Model):
    """
    Hold Pollutant data
    """
    key = models.CharField(primary_key=True, max_length=16)
    copernicus_key = models.CharField(max_length=16, null=True, db_index=True)
    observation_key = models.CharField(max_length=16, null=True, db_index=True)
    eea_key = models.CharField(max_length=16, null=True, db_index=True)

    def __str__(self):
        return self.key

    @staticmethod
    def get_keys():
        """
        Return the list of pollutant keys supported by the database
        :return:
        """
        qs = Pollutant.objects.all()
        return {p.key for p in qs}

    @staticmethod
    def get(pollutant: str) -> str:
        """
        Retrieve the pollutant key no matter which name is provided by the source.
        The argument provided is case insensitive.
        :param pollutant: Any string used to describe a pollutant
        :return: The key value used in the application for pollutant
        """
        try:
            rv = Pollutant.objects.get(Q(copernicus_key__iexact=pollutant) |
                                       Q(observation_key__iexact=pollutant) |
                                       Q(eea_key__iexact=pollutant) |
                                       Q(key__iexact=pollutant))
        except ObjectDoesNotExist as e:
            logging.info(f"'{pollutant}' is not supported.")
            return None

        return rv.key

    @staticmethod
    def get_eea_pollutants() -> dict:
        pollutants_lookup = {}
        pollutants = Pollutant.objects.filter(eea_key__isnull=False)
        for p in pollutants:
            pollutants_lookup.update({p.eea_key: p})

        return pollutants_lookup

    @staticmethod
    def get_copernicus_pollutants() -> dict:
        pollutants_lookup = {}
        pollutants = Pollutant.objects.filter(copernicus_key__isnull=False)
        for p in pollutants:
            pollutants_lookup.update({p.copernicus_key: p})

        return pollutants_lookup

    @staticmethod
    def get_observation_pollutants(pollutants: list = None) -> dict:
        pollutants_lookup = {}

        # get all if no argument provided
        if pollutants is None:
            p_objs = Pollutant.objects.filter(observation_key__isnull=False)
        # only get the ones in the list
        # any key may have been provided - get the object for it
        else:
            p_objs = Pollutant.objects.filter(Q(copernicus_key__in=pollutants) |
                                              Q(observation_key__in=pollutants) |
                                              Q(eea_key__in=pollutants) |
                                              Q(key__in=pollutants))

        for p in p_objs:
            pollutants_lookup.update({p.observation_key: p})

        return pollutants_lookup

    @staticmethod
    def get_all_targets(years: list = None, country_codes: list = None, pollutants: list = None) -> dict:
        """
        Get targets for all pollutants.
        Targets aren't tracked by country or year in the application.
        Targets apply all countries to all years equally.
        If a list of years is required, a list of countries is optional.
        If no countries are provided, all EU countries are returned.
        """
        # get country codes
        if country_codes is None:
            country_codes = EU_ISOCODES
        else:
            country_codes = [c.upper() for c in country_codes]

        if years is None:
            years = [y for y in range(2016, 2025)]

        if pollutants is None:
            pollutants = Pollutant.get_keys()
        else:
            pollutants = [p.upper() for p in pollutants]

        p_objs = Pollutant.objects.filter(key__in=pollutants)

        targets = {}
        for p_obj in p_objs:
            t = p_obj.targets.values()
            if len(t) == 0:
                continue

            _t_dict = {}
            for _t in t:
                msmt = _t['measurement_id']
                del _t['id']
                del _t['measurement_id']
                del _t['pollutant_id']
                _t_dict.update({msmt: _t})

            targets.update({p_obj.key: _t_dict})

        return {c: {y: targets for y in years} for c in country_codes}

    @staticmethod
    def get_targets_df(years: list = None, country_codes: list = None, pollutants: list = None) -> pd.DataFrame:
        if country_codes is None:
            country_codes = EU_ISOCODES
        if pollutants is None:
            pollutants = Pollutant.get_keys()
        if years is None:
            years = [y for y in range(2016, 2025)]

        root_df = pd.DataFrame(Target.objects.filter(pollutant__in=pollutants).values()).drop(columns=['id'])
        rv_df = pd.DataFrame()
        for c in country_codes:
            for y in years:
                temp_df = root_df
                temp_df['country'] = c
                temp_df['year'] = y
                rv_df = rv_df.append(temp_df)

        rv_df = rv_df.reset_index(drop=True)
        return rv_df


    @staticmethod
    def get_pollutant_dayavg_by_station_df(date_from: str, date_to: str, pollutant: str):
        # check pollutant
        pollutant = Pollutant.get(pollutant)
        if pollutant is None:
            return JsonResponse(f"Pollutant '{pollutant}' not a supported pollutant.", safe=False)

        # parse dates
        s_year, s_month, s_day = [int(s) for s in date_from.split('-')]
        e_year, e_month, e_day = [int(s) for s in date_to.split('-')]

        tz = pytz.timezone("CET")
        date_from = datetime.datetime(year=s_year, month=s_month, day=s_day, tzinfo=tz)  # '2020-01-01'
        date_to = datetime.datetime(year=e_year, month=e_month, day=e_day, tzinfo=tz)  # '2020-04-30'

        readings_rs = Pollutant.objects.get(pk=pollutant).readings.filter(date_time__gte=date_from,
                                                                          date_time__lte=date_to, validity=1).values(
            'air_quality_station_id',
            'pollutant_id').annotate(Avg('value'))
        readings_df = pd.DataFrame(readings_rs).rename(columns={'air_quality_station_id': 'air_quality_station'})
        return readings_df


class Target(models.Model):
    """
    Holds pollutant targets
    """
    unit = models.CharField(max_length=16)
    value = models.FloatField()
    count_limit = models.IntegerField(null=True)
    measurement = models.ForeignKey(Measurement, on_delete=models.DO_NOTHING, related_name='targets', null=True)
    pollutant = models.ForeignKey(Pollutant, on_delete=models.DO_NOTHING, related_name='targets', null=True)

    def __str__(self):
        return f"{self.pollutant}: \n\t{'value':13}: {self.value} \n\t{'count_limit':13}: {self.count_limit}  \n\t{'measurment':13}: {self.measurement}"

    def get(self):
        return self.measurement.measurement, \
               {'value': self.value, 'count_limit': self.value, 'unit': self.unit}
