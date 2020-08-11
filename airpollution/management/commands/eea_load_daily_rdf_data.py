"""
author: Hemant Bajpai
This module will load RDF data from EEA source.
This command takes couple of hours to run so it is supposed to be done once a day.
Usage: python manage.py eea_load_daily_rdf_data
"""
import os
from django.core.management.base import BaseCommand
from eugreendeal.settings import MEDIA_ROOT
from dataingestor.EEA.EEADataSource import EEADataSource


class Command(BaseCommand):
    help = "Load daily EEA rdf data into the database."

    def add_arguments(self, parser):
        def_path = os.path.join(MEDIA_ROOT, 'media')
        parser.add_argument('-d', '--target_dir', nargs='?', type=str, default=def_path)

    def handle(self, *args, **options):
        print(f"Saving files to: {options['target_dir']}")
        api = EEADataSource(name='EEA Data Source')
        api.load_data(**options)
