"""
author: Hemant Bajpai
This module will load the application database to include EEA data
based on files that are already available.
Usage: python manage.py eea_load_db_from_files
"""
import os
from django.core.management.base import BaseCommand
from eugreendeal.settings import MEDIA_ROOT
from dataingestor.EEA.EEADataSource import EEADataSource
from airpollution.models.models_eea import EEADataModel


class Command(BaseCommand):
    help = "Load existing EEA data files into the database."

    def handle(self, *args, **options):
        for cop_obj in EEADataModel.objects.all():
            cop_obj.delete()

        def_path = os.path.join(MEDIA_ROOT, 'media')
        fpath = os.path.join(def_path, "EEA_RDF_Complete_DATA.csv")

        api = EEADataSource(name='EEA Data Source')
        api.load_db_from_file(fpath)
