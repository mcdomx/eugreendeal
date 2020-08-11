"""
Author: Hemant Bajpai
This script includes models that support data
originating from the EEA dataset.
"""
from django.db import models

from airpollution.models.models_nuts import NutsRegions

RECENT_VERSION = 2019
class EurostatDataModel(models.Model):
    """
    Each record holds parameters of data that are contained in a file.
    """
    year = models.IntegerField(db_index=True)
    population = models.IntegerField()
    nutsRegionStr = models.CharField(max_length=20, db_index=True)
    nutsRegion = models.ForeignKey(NutsRegions, on_delete=models.CASCADE, related_name='nuts2_population', null=True)

    @staticmethod
    def get_population_info(nuts_2: str,
                         year: int = RECENT_VERSION):
        """
        Returns map of data based on input request
        :param nuts_2: nuts region 2 code
        :param year: year.
        :return: The results will filter model based on these arguments.
        """

        qs = EurostatDataModel.objects.filter(nutsRegionStr=nuts_2, year=year)
        rv = {}
        for r in qs:
            rv.update({nuts_2: r.population})

        return rv