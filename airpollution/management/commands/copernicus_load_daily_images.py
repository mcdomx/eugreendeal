"""
author: Mark McDonald
This module will load a day's images from the copernicus api.
If the date is not specified, the prior day will be downloaded.
Usage: python manage.py copernicus_load_daily_images
"""
import datetime
import logging
from django.core.management.base import BaseCommand
from dataingestor.copernicus.CopernicusDataSource import CopernicusDataSource


class Command(BaseCommand):
    help = "Load daily Copernicus image files into the database."

    def add_arguments(self, parser):

        parser.add_argument('-t', '--token', nargs='?', type=str, default=None)
        parser.add_argument('-d', '--target_dir', nargs='?', type=str)
        parser.add_argument('-c', '--category', nargs='+', type=str)
        parser.add_argument('-l', '--levels', nargs='+', type=str)
        parser.add_argument('-r', '--reference_time', nargs='?', type=str)  # YYYY-MM-DD
        parser.add_argument('-s', '--since_date', nargs='?', type=str)  # YYYY-MM-DD

    def handle(self, *args, **options):

        # set verbosity
        verbosity = options.get('verbosity', 0)
        v_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
        options.update({'verbosity': v_map.get(verbosity, 0)})

        logger = logging.getLogger("load_satellite_images")
        logger.setLevel(level=options.get('verbosity', logging.ERROR))

        token = options.get('token', None)

        # format reference time - if no time give, use yesterday
        reference_time = options.get('reference_time', None)
        yesterday = (datetime.datetime.today() - datetime.timedelta(1)).isoformat().split('T')[0]
        if reference_time is None:
            reference_time = yesterday

        ref_date = datetime.date(year=int(reference_time.split('-')[0]),
                                 month=int(reference_time.split('-')[1]),
                                 day=int(reference_time.split('-')[2]))
        yesterday_date = (datetime.date.today() - datetime.timedelta(1))
        days = (yesterday_date-ref_date).days
        if days > 30 or days < 0:
            logger.error("Files are only available for 30 days in the past.")
            return None

        if len(reference_time) != 10:
            logger.error("Mal formed date.  Please format date as YYYY-MM-DD.")
            return None

        since_date = options.get('since_date')

        if since_date is not None:
            # check for mal formed date
            if len(reference_time) != 10:
                logger.error("Mal formed since_date.  Please format date as YYYY-MM-DD.")
                return None
            # if since date is more than 30 days, change to -30 days as first date
            since_day = datetime.date(year=int(since_date.split('-')[0]),
                                      month=int(since_date.split('-')[1]),
                                      day=int(since_date.split('-')[2]))
            yesterday_date = (datetime.date.today() - datetime.timedelta(1))
            days = (yesterday_date-since_day).days
            if days > 30:
                days = 30

            api = CopernicusDataSource(name='Copernicus Data Source', logger=logger, token=token)
            for d in reversed(range(0, days)):
                load_date = (datetime.date.today() - datetime.timedelta(d)).isoformat().split('T')[0]
                print(f"Loading date: {load_date}")
                options.update({'reference_time': f"{load_date}T00:00:00Z"})
                api.load_data(**options)
        else:
            options.update({'reference_time': f"{reference_time}T00:00:00Z"})
            api = CopernicusDataSource(name='Copernicus Data Source', logger=logger)
            api.load_data(**options)
