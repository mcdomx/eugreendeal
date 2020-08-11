"""
author: Mark McDonald
This module will load tmeta data for pollution observation stations.
Usage: python manage.py load_eea_station_data --year_from 2019 --year_to 2020 --load_from_file 1
"""
import logging
import os

from django.core.management.base import BaseCommand
from dataingestor.EEA.EEAObservationStationDataSource import EEAStationDataSource
from dataingestor.EEA.EEAObservationReadingDataSource import ReadingDataSource
from eugreendeal.settings import MEDIA_ROOT

class Command(BaseCommand):
    help = "Load new metadata for EEA observation stations.  File must be located in 'media/observation_data' directory. Then load observations."

    def add_arguments(self, parser):
        parser.add_argument('--filename', nargs='?', type=str, default='PanEuropean_metadata.csv')
        parser.add_argument('--year_from', nargs='?', type=int, default=0)
        parser.add_argument('--since_date', nargs='?', type=str, default='')
        parser.add_argument('--year_to', nargs='?', type=int, default=0)
        parser.add_argument('--month', nargs='?', type=int, default=0)
        parser.add_argument('--country_codes', nargs='+', type=str, default='')
        parser.add_argument('--pollutants', nargs='+', type=str, default='')
        parser.add_argument('--stations', nargs='+', type=str, default='')
        parser.add_argument('--meta_url', nargs='?', type=str, default='')
        parser.add_argument('--meta_targetdir', nargs='?', type=str, default='')
        parser.add_argument('--load_from_file', nargs='?', type=bool, default=False)
        parser.add_argument('--skip_stations', nargs='?', type=bool, default=False)
        parser.add_argument('--dummy', nargs='?', type=bool, default=False)
        parser.add_argument('--n', nargs='?', type=int, default=1)
        parser.add_argument('--frac', nargs='?', type=float, default=None)
        parser.add_argument('--level', nargs='?', type=int, default=0)

    def handle(self, *args, **options):

        # check that from and to year are the same if month is provided
        m = options.get('month')
        if m != 0:
            yrf = options.get('year_from')
            yrt = options.get('year_to')
            if yrf != yrt:
                logging.error("If loading a month, the year_from and year_to must be the same.")
                return

            if m < 0 or m > 12:
                logging.error("Month must be between 1 and 12.")
                return

        if not options.get('meta_url'):
            options.update({'url': 'http://discomap.eea.europa.eu/map/fme/metadata/PanEuropean_metadata.csv'})

        if not options.get('meta_targetdir'):
            options.update({'target_dir': os.path.join(MEDIA_ROOT, 'observation_data')})

        if options.get('dummy'):
            options.update({'dummy': True})

        # reset verbosity argument with global verbosity level
        logger = options.get('logger', None)
        if logger is None:
            verbosity = options.get('verbosity', 0)
            v_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
            options.update({'verbosity': v_map.get(verbosity, 0)})

            logger = logging.getLogger("load_data")
            logger.setLevel(level=options.get('verbosity', logging.ERROR))

        if not options.get('skip_stations'):
            # LOAD STATIONS
            logger.info("Loading station meta-data ... ")
            if options.get('load_from_file'):
                logger.debug("\tLoading from file.")
            station_api = EEAStationDataSource(name='EEA Station Data Source', logger=logger)
            station_api.load_data(**options)
            logger.info("Done loading station meta-data")

        # LOAD READINGS
        logger.debug("Loading station readings ... ")
        data_api = ReadingDataSource(name='Station Readings Data Source', logger=logger)
        if options.get('dummy', False):
            data_api.load_dummy_data(**options)
        else:
            data_api.load_data(**options)
