"""
author: Hemant Bajpai
This module will load population data from eurostat source.
Usage: python manage.py load_eurostat_population_data
"""
import os
from eugreendeal.settings import MEDIA_ROOT
from django.core.management.base import BaseCommand
from dataingestor.Eurostat.EurostatDataSource import EurostatDataSource


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        def_path = os.path.join(MEDIA_ROOT, 'media')
        parser.add_argument('-d', '--target_dir', nargs='?', type=str, default=def_path)

    def handle(self, *args, **options):
        print(f"Saving files to: {options['target_dir']}")
        ds = EurostatDataSource(name="eurostat")
        ds.load_data(**options)