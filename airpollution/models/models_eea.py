"""
Author: Hemant Bajpai
This script includes models that support data
originating from the EEA dataset.
"""
from django.db import models
from django.db.models import Sum

from airpollution.models.models_nuts import NutsRegions
from airpollution.models.models_pollutants import Pollutant


class EEADataModel(models.Model):
    """
    Each record holds parameters of data that are contained in a file.
    """
    year = models.IntegerField(db_index=True)
    pollutant_name = models.CharField(max_length=20, db_index=True)
    pollutant = models.ForeignKey(Pollutant, on_delete=models.DO_NOTHING, null=True, related_name="eea_data",
                                  db_index=True)
    unit = models.CharField(max_length=20)
    country = models.CharField(max_length=20, db_index=True)
    country_code = models.ForeignKey(NutsRegions, on_delete=models.DO_NOTHING, null=True, related_name="eea_data",
                                     db_index=True)
    sector = models.CharField(max_length=20, db_index=True)
    sector_group = models.CharField(max_length=100, db_index=True)
    emissions = models.DecimalField(decimal_places=2, max_digits=25)

    @staticmethod
    def get_sectors_info(year: int = 0,
                         country_code: str = None,
                         sector_group: str = None,
                         pollutant: str = None):
        """
        Returns map of data based on input request
        :param year: year
        :param country_code: country_code
        :param sector_group: sector_group
        :param pollutant: pollutant.
        :return: The results will filter model based on these arguments.
        """
        if sector_group:
            qs = EEADataModel.objects.filter(sector_group=sector_group)
        else:
            qs = EEADataModel.objects.all()

        if country_code:
            qc = qs.filter(country=country_code)
        else:
            qc = qs

        if type(year) == int:
            qy = qc.filter(year=year)
        else:
            qy = qc

        if pollutant:
            qp = qy.filter(pollutant_name=pollutant)
        else:
            qp = qy

        # getting values based on groupby
        query_set = qp.values('year', 'pollutant_name', 'country', 'sector_group').annotate(total_emissions=Sum('emissions'))
        rv = {}

        # creating map to return
        for obj in query_set:
            if obj['country'] in rv:
                if obj['year'] in rv[obj['country']]:
                    if obj['pollutant_name'] in rv[obj['country']][obj['year']]:
                        rv[obj['country']][obj['year']][obj['pollutant_name']][obj['sector_group']] = obj['total_emissions']
                    else:
                        rv[obj['country']][obj['year']][obj['pollutant_name']] = {}
                        rv[obj['country']][obj['year']][obj['pollutant_name']][obj['sector_group']] = obj['total_emissions']
                else:
                    rv[obj['country']][obj['year']] = {}
                    rv[obj['country']][obj['year']][obj['pollutant_name']] = {}
                    rv[obj['country']][obj['year']][obj['pollutant_name']][obj['sector_group']] = obj['total_emissions']
            else:
                rv[obj['country']] = {}
                rv[obj['country']][obj['year']] = {}
                rv[obj['country']][obj['year']][obj['pollutant_name']] = {}
                rv[obj['country']][obj['year']][obj['pollutant_name']][obj['sector_group']] = obj['total_emissions']

        return rv