"""
Author: Hemant Bajpai
RDF EEA Data source which has emissions value based on country, year, pollutant and sector.

"""
import csv
import gzip
import logging
import multiprocessing
import os
import urllib.request
import mmap
from multiprocessing.pool import Pool

import rdflib
from django.db import transaction

from airpollution.models.models_eea import EEADataModel
from dataingestor.DataSource import DataSource

logging.basicConfig(level=logging.INFO)

sectors_map = {
    "Agriculture": set(["3B1a", "3B1b", "3B2", "3B3", "3B4a", "3B4d", "3B4e", "3B4f", "3B4gi", "3B4gii", "3B4giii",
                        "3B4giv", "3B4h", "3Da1", "3Da2a", "3Da2b", "3Da2c", "3Da3", "3Da4", "3Db", "3Dc", "3Dd", "3De",
                        "3Df", "3F", "3I"]),
    "Commercial, institutional and households": set(["1A4ai", "1A4aii", "1A4bi", "1Ab4ii", "1A4ci", "1A4cii", "1A5a",
                                                     "1A5b"]),
    "Energy production and distribution": set(["1A1a", "1A1b", "1A1c", "1B1a", "1B1b", "1B1c", "1B2ai", "1B2aiv",
                                               "1B2av", "1B2b", "1B2c", "1B2d"]),
    "Energy use in industry": set(["1A2a", "1A2b", "1A2c", "1A2d", "1A2e", "1A2f", "1A2gvii", "1A2gviii"]),
    "Industrial processes and product use": set(["2A1", "2A2", "2A3", "2A5a", "2A5b", "2A5c", "2A6", "2B1", "2B10a",
                                                 "2B10b", "2B2", "2B3", "2B5", "2B6", "2B7", "2C1", "2C2", "2C3", "2C4",
                                                 "2C5", "2C6", "2C7a", "2C7b", "2C7c", "2C7d", "2D3a", "2D3b", "2D3c",
                                                 "2D3d", "2D3e", "2D3f", "2D3g", "2D3h", "2D3i", "2G", "2H1", "2H2",
                                                 "2H3", "2I", "2J", "2K", "2L"]),
    "NATIONAL_TOTAL": set(["NATIONAL_TOTAL"]),
    "Non-road transport": set(["1A3ai(i)", "1A3aii(i)", "1A3c", "1A3di(ii)", "1A3dii", "1A3ei", "1A3eii", "1A4ciii"]),
    "Other": set(["6A"]),
    "Road transport": set(["1A3bi", "1A3bii", "1A3biii", "1A3biv", "1A3bv", "1A3bvi", "1A3bvii"]),
    "Waste": set(["5A", "5B1", "5B2", "5C1a", "5C1bi", "5C1bii", "5C1biii", "5C1biv", "5C1bv", "5C1bvi", "5C2", "5D1",
                  "5D2", "5D3", "5E"])
}


class EEADataSource(DataSource):

    def __init__(self, name: str, description: str = None):
        """
        Initializes the class
        """
        DataSource.__init__(self, name, description)

    def load_data(self, **kwargs) -> None:
        """
        Load RDF data from EEA data source
        :param kwargs: kwargs.
        """

        # getting the RDF file
        target_dir = kwargs.get('target_dir')
        baseurl = "http://r.eionet.europa.eu/rdfdumps/clrtap_nec_unfccc/"
        filename = "clrtap_nfr09_gf.rdf.gz"
        outfilepath = filename[:-3]

        response = urllib.request.urlopen(baseurl + filename)
        with open(outfilepath, 'wb') as outfile:
            outfile.write(gzip.decompress(response.read()))

        # creating RDF graph
        pollution_graph = rdflib.Graph()
        pollution_graph.parse(file=open(outfilepath, 'r'), format='xml')

        # performing SPARQL query
        results = pollution_graph.query("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX clrtap_nec_unfccc: <http://reference.eionet.europa.eu/clrtap_nec_unfccc/schema/>
        PREFIX country: <http://reference.eionet.europa.eu/clrtap_nec_unfccc/country/>
        PREFIX sector: <http://reference.eionet.europa.eu/clrtap_nec_unfccc/clrtap_nec_nfr09_sector/> 

        SELECT
        ?pollutant_name
        ?country_code
        ?year
        ?sector_code
        ?unit
        ?emissions

        WHERE {{  

           #?clrtap_nfr09_gf clrtap_nec_unfccc:country_code ?country_code .
           #?clrtap_nfr09_gf clrtap_nec_unfccc:pollutant_name ?pollutant_name .
           #?clrtap_nfr09_gf clrtap_nec_unfccc:year ?year .
              ?clrtap_nfr09_gf clrtap_nec_unfccc:country_code ?country_code .
              ?clrtap_nfr09_gf clrtap_nec_unfccc:pollutant_name ?pollutant_name .
              ?clrtap_nfr09_gf clrtap_nec_unfccc:sector_code ?sector_code .
              ?clrtap_nfr09_gf clrtap_nec_unfccc:unit ?unit .
              ?clrtap_nfr09_gf clrtap_nec_unfccc:year ?year .
              ?clrtap_nfr09_gf clrtap_nec_unfccc:emissions ?emissions .  

           FILTER (?year = '2017')
           FILTER (?pollutant_name in ('SOx', 'NOx', 'NMVOC', 'CO'))
           #to be changed with EEA33
           FILTER (?country_code in (country:EU28, country:TR, country:IS, country:NO, country:LI, country:CH))
           #FILTER (?country_code in (country:EEA33))

         }
         }

         """)

        # create a full path to save file to
        fpath = os.path.join(target_dir, "EEA_RDF_Complete_DATA.csv")

        with open(fpath, 'w', newline='') as file:
            writer = csv.writer(file)
            for row in results:
                p = str(row.asdict()['pollutant_name'].toPython())
                y = str(row.asdict()['year'].toPython())
                u = str(row.asdict()['unit'].toPython())
                e = str(row.asdict()['emissions'].toPython())
                c = row.asdict()['country_code']
                s = row.asdict()['sector_code']
                writer.writerow([p, y, ext(c), ext(s), e, u])

    def load_dummy_data(self):
        """
        No implementation for EurostatDataSource.
        """
        pass

    @staticmethod
    def load_db_from_file(filepath: str) -> None:
        """
        Loads data from file
        :param filepath: path of the file to load
        """
        BATCH_RECORD_COUNT = 10000

        for obj in EEADataModel.objects.all():
            obj.delete()

        with open(filepath, "r+b") as f:
            map_file = mmap.mmap(f.fileno(), 0)
            record_line_number = []
            for i, _ in enumerate(iter(map_file.readline, b"")):
                if i == 0 or i % BATCH_RECORD_COUNT == 0:
                    record_line_number.append((i, BATCH_RECORD_COUNT, filepath))

        ## Serial processing
        for data in record_line_number:
            process_file_chunk(data)


def process_file_chunk(data: tuple):
    """
    This is for batch loading
    :param data: data to load
    """
    logging.info('Received data {} for processing'.format(str(data)))
    filepath = data[2]
    start_line_num = data[0]
    end_line_num = start_line_num + data[1]

    with open(filepath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        records = []
        for i, row in enumerate(csv_reader):
            if i == 0 or i < start_line_num:
                continue
            if i >= end_line_num:
                break

            try:
                emission_value = float(row[4])
            except:
                logging.error('Error in converting to float. {}'.format(row))
                continue

            record = EEADataModel.objects.create(year=row[1],
                                                 pollutant_name=row[0],
                                                 unit=row[5],
                                                 country=row[2],
                                                 sector=row[3],
                                                 sector_group=get_sector_group(row[3]),
                                                 emissions=emission_value)
            records.append(record)

        logging.info('Processing lines {} to {}'.format(start_line_num, i - 1))
        with transaction.atomic():
            EEADataModel.objects.bulk_create(records, ignore_conflicts=True)
        logging.info('Processed lines {} to {}'.format(start_line_num, i - 1))

#######################
# SUPPORT FUNCTIONS
#######################


def get_sector_group(sector_code) -> str:
    """
    Gets sector group information
    :param sector_code: sector code
    :return: returns the sector group information
    """
    if sector_code in sectors_map["Agriculture"]:
        return "Agriculture"
    elif sector_code in sectors_map["Commercial, institutional and households"]:
        return "Commercial, institutional and households"
    elif sector_code in sectors_map["Energy production and distribution"]:
        return "Energy production and distribution"
    elif sector_code in sectors_map["Energy use in industry"]:
        return "Energy use in industry"
    elif sector_code in sectors_map["Industrial processes and product use"]:
        return "Industrial processes and product use"
    elif sector_code in sectors_map["Road transport"]:
        return "Road transport"
    elif sector_code in sectors_map["Non-road transport"]:
        return "Non-road transport"
    elif sector_code in sectors_map["Other"]:
        return "Other"
    elif sector_code in sectors_map["Waste"]:
        return "Waste"
    else:
        return "NATIONAL_TOTAL"


def extract_name(uri) -> str:
    """
    Parse the trailing text from a uri.
    If argument is not a uri, returns the initial value.
    :param uri: uri to extract name
    :return: returns the extracted name
    """

    if type(uri) == rdflib.term.URIRef:
        uri = uri.toPython()

    if uri[-1] != '/':
        uri = uri.split('/')[-1]

    if uri[-1] != '#':
        uri = uri.split('#')[-1]

    return uri


def ext(uri) -> str:
    """
    Shortcut function for extract_name()
    :param uri: uri to extract name
    :return: returns the extracted name
    """
    return extract_name(uri)
