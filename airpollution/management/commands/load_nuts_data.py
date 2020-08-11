"""
author: Mark McDonald
This module will load NUTS data from locally stored files
Usage: python manage.py load_nuts_data
"""
import logging
import os

from django.core.management.base import BaseCommand
from dataingestor.nuts.NutsDataSource import NutsDataSource
from eugreendeal.settings import MEDIA_ROOT

# logging.basicConfig(level=logging.DEBUG)


class Command(BaseCommand):
    help = "Load NUTS map data from geojson files.  " \
           "JSON files must come from File must be located in 'media/observation_data' directory. Then load observations."

    def add_arguments(self, parser):
        parser.add_argument('--filepath', nargs='?', type=str, default=MEDIA_ROOT)
        parser.add_argument('--year', nargs='?', type=int, default=2016)
        parser.add_argument('--crs', nargs='?', type=int, default=4326)
        parser.add_argument('--nuts_level', nargs='?', type=str, default=3)

    def handle(self, *args, **options):
        year = options.get('year')
        crs = options.get('crs')
        nuts_level = options.get('nuts_level')

        # reset verbosty argument with global verbosity level
        verbosity = options.get('verbosity', 0)
        v_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
        options.update({'verbosity': v_map.get(verbosity, 0)})

        logger = logging.getLogger("load_nuts")
        logger.setLevel(level=options.get('verbosity', logging.ERROR))

        if not year or not crs or not nuts_level:
            logger.info("Missing arguments.  year, crs and nuts_level are all required.")
            logger.info(options)

        logger.debug("Arguments:")
        for k, v in options.items():
            logger.debug(f"{k}: {v}")

        nuts_api = NutsDataSource(name='NUTS Data Source', logger=logger)
        nuts_api.load_data(year=year, crs=crs, nuts_level=nuts_level)
