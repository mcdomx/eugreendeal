import os
import random
import logging

from django.core.management.base import BaseCommand
from django.core.management import call_command

from eugreendeal.settings import MEDIA_ROOT

from airpollution.models.models import EUStat, EUCountryCode
from dataingestor.copernicus.CopernicusDataSource import TARGET_DIR
from dataingestor.EEA.EEADataSource import EEADataSource


class Command(BaseCommand):
    """
    Command class to populate db from scratch.
    """

    args = 'no args required'
    help = 'populate DB with initial dummy values'

    @staticmethod
    def create_some_dummy_data():

        for eu_obj in EUCountryCode.objects.all():
            eu_obj.delete()

        country_codes = [('AT', 'Austria'), ('BE', 'Belgium'), ('BG', 'Bulgaria'), ('CY', 'Cyprus'),
                         ('CZ', 'Czech Republic'),
                         ('DE', 'Germany'), ('DK', 'Denmark'), ('EE', 'Estonia'), ('ES', 'Spain'), ('FI', 'Finland'),
                         ('FR', 'France'), ('GR', 'Greece'), ('HR', 'Croatia'), ('HU', 'Hungary'), ('IE', 'Ireland'),
                         ('IT', 'Italy'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('LV', 'Latvia'), ('MT', 'Malta'),
                         ('NL', 'Netherlands'), ('PO', 'Poland'), ('PT', 'Portugal'), ('RO', 'Romania'),
                         ('SE', 'Sweden'), ('NO', 'Norway'), ('IS', 'Iceland'),
                         ('SI', 'Slovenia'), ('SK', 'Slovakia'), ('GI', 'Gibraltar'),
                         ('UK', 'United Kingdom')]

        for country_code_tuple in country_codes:
            # eu_country_code_obj = EUCountryCode(country_code=country_code_tuple[0],
            # country_name=country_code_tuple[1])
            eu_country_code_obj = EUCountryCode.objects.create(country_code=country_code_tuple[0],
                                                               country_name=country_code_tuple[1])
            eu_country_code_obj.save()

        for i in range(2000, 2016):
            eustat = EUStat.objects.create(year=i, pollutant_name='CO2', unit='Gg',
                                           country=EUCountryCode.objects.filter(country_code='FI')[0],
                                           emissions=random.randint(100, 200))
            eustat.save()

    def handle(self, *args, **options):
        # reset verbosity argument with global verbosity level
        verbosity = options.get('verbosity', 0)
        # v_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
        # options.update({'verbosity': v_map.get(verbosity, 0)})
        #
        # logger = logging.getLogger("populate_db")
        # logger.setLevel(level=options.get('verbosity', logging.ERROR))

        # self.create_some_dummy_data()

        # LOAD NUTS DATA
        logging.info("######### Loading NUTS data ...")
        call_command('load_nuts_data', verbosity=verbosity)
        logging.info("######### Done loading NUTS data!")

        # LOAD POLLUTANTS
        logging.info("######### Loading Pollutants data ...")
        call_command('load_pollutants', verbosity=verbosity)
        logging.info("######### Done loading Pollutants data!")

        # LOAD OBSERVATION STATIONS - requires NUTS load first
        logging.info("######### Loading Pollutant Station data ...")
        call_command('load_eea_station_data', dummy=True, year_from=2019, year_to=2020, level=1, verbosity=verbosity)
        logging.info("######### Done loading Pollutant Station data!")

        # LOAD SATELLITE IMAGES FROM EXISTING FILES
        # if no files exist - download images from yesterday

        os.makedirs(TARGET_DIR, exist_ok=True)
        if len(os.listdir(TARGET_DIR)) == 0:
            logging.info("######### Downloading daily satellite images ...")
            call_command('copernicus_load_daily_images')
            logging.info("######### Done downloading daily satellite images!")

        logging.info("######### Loading satellite image data ... ")
        call_command('copernicus_load_db_from_files')
        logging.info("######### Done loading satellite image data!")

        # LOAD DATA FROM LOCAL EEA FILES
        logging.info("######### Loading EEA data ... ")
        def_path = os.path.join(MEDIA_ROOT, 'media')
        fpath = os.path.join(def_path, "EEA_RDF_Complete_DATA.csv")
        api = EEADataSource(name='EEA Data Source')
        api.load_db_from_file(fpath)
        logging.info("######### Done loading EEA data!")
