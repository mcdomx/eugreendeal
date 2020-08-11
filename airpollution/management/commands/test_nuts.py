"""
author: Mark McDonald
For testing
"""
import logging
import os

from django.core.management.base import BaseCommand
from dataingestor.nuts.NutsDataSource import NutsDataSource
from airpollution.views.nuts_maps_views import _md
from eugreendeal.settings import MEDIA_ROOT

# logging.basicConfig(level=logging.DEBUG)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        # parser.add_argument('--filepath', nargs='?', type=str, default=MEDIA_ROOT)
        parser.add_argument('--year', nargs='?', type=int, default=2016)
        parser.add_argument('--crs', nargs='?', type=int, default=4326)
        parser.add_argument('--nuts_level', nargs='?', type=str, default=3)

    def handle(self, *args, **options):
        year = options.get('year')
        crs = options.get('crs')
        nuts_level = options.get('nuts_level')

        if not year or not crs or not nuts_level:
            logging.info("Missing arguments.  year, crs and nuts_level are all required.")
            logging.info(options)

        logging.info("Arguments:")
        for k, v in options.items():
            logging.info(f"{k}: {v}")

        print(_md.df)
