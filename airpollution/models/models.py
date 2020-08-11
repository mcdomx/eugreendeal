from django.contrib.auth.models import Group

from django.db import models

Group.add_to_class('description', models.CharField(max_length=180, null=True, blank=True))


class ChartViz(models.Model):
    chart_id = models.CharField(max_length=128, db_index=True)
    url = models.CharField(max_length=2048, blank=True, null=True)
    label = models.CharField(max_length=2048, blank=True, null=True)
    groups = models.ManyToManyField(Group, db_index=True)


class EUCountryCode(models.Model):
    country_code = models.CharField(max_length=2, db_index=True)
    country_name = models.CharField(max_length=20)

    def __str__(self):
        return ':'.join([self.country_code, self.country_name])


class EUStat(models.Model):
    year = models.IntegerField(db_index=True)
    pollutant_name = models.CharField(max_length=20, db_index=True)
    unit = models.CharField(max_length=20)
    country = models.ForeignKey(EUCountryCode, on_delete=models.CASCADE, blank=False, null=True, db_index=True)
    emissions = models.DecimalField(decimal_places=2, max_digits=6)

    def __str__(self):
        return ':'.join([str(self.country.country_name), str(self.year), self.pollutant_name])

