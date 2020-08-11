"""
author: Mark McDonald
This module will load the application database to include copernicus data
based on files that are already available.
Usage: python manage.py copernicus_load_db_from_files
"""
from django.core.management.base import BaseCommand
from eugreendeal.settings import MEDIA_ROOT
from dataingestor.copernicus.CopernicusDataSource import CopernicusDataSource


class Command(BaseCommand):
    help = "Load existing Copernicus data files into the database. --root_path = search for files under this path (def: MEDIA_ROOT).  --ext = search for files with this extenstion (def: '.nc)."

    def add_arguments(self, parser):
        parser.add_argument('--root_path', nargs='?', type=str, default=MEDIA_ROOT)
        parser.add_argument('--ext', nargs='?', type=str, default='.nc')

    def handle(self, *args, **options):
        api = CopernicusDataSource(name='Copernicus Data Source', logger=None)
        api.load_db_from_files()
