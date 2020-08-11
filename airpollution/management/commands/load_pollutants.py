"""
author: Mark McDonald
"""

import logging

from django.core.management.base import BaseCommand
from dataingestor.PollutantDataSource import PollutantDataSource


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # reset verbosty argument with global verbosity level
        logger = options.get('logger', None)
        if logger is None:
            verbosity = options.get('verbosity', 0)
            v_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
            options.update({'verbosity': v_map.get(verbosity, 0)})

            logger = logging.getLogger("load_data")
            logger.setLevel(level=options.get('verbosity', logging.ERROR))

        ds = PollutantDataSource(logger=logger)
        ds.load_data(**options)







