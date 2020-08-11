"""
Author: Hemant Bajpai
Population data source, includes information of population based in nuts 2 region
by years.

"""
import csv
import gzip
import logging

import requests
from airpollution.models.models_nuts import NutsRegions
from airpollution.models import EurostatDataModel
from dataingestor.DataSource import DataSource


class EurostatDataSource(DataSource):

    def __init__(self, name: str, description: str = None):
        """
        Initializes the class
        """
        DataSource.__init__(self, name, description)

    def load_data(self, **kwargs) -> None:
        """
        Load population data from eurostat data source based on nuts 2 region.
        :param kwargs: kwargs.
        """
        # erase everything first
        for t in EurostatDataModel.objects.all():
            t.delete()

        # downloading url
        url = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/tgs00096.tsv.gz"

        r = requests.get(url)

        fname = url.split('/')[-1]
        outfilepath = fname[:-3]

        try:
            # putting data into model
            with open(outfilepath, "wb") as f:
                f.write(gzip.decompress(r.content))
            with open(outfilepath) as tsvfile:
                reader = csv.reader(tsvfile, delimiter='\t')
                next(reader)
                for row in reader:
                    nutsRegionStr = row[0].split(',')[3]

                    if NutsRegions.objects.filter(NUTS_ID=nutsRegionStr).exists():
                        nutsRegion = NutsRegions.objects.get(NUTS_ID=nutsRegionStr)

                        record = EurostatDataModel.objects.create(year=2008,
                                                              population=_get_pollution_value(row[1]),
                                                              nutsRegionStr=nutsRegionStr,
                                                              nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2009,
                                                                  population=_get_pollution_value(row[2]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2010,
                                                                  population=_get_pollution_value(row[3]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2011,
                                                                  population=_get_pollution_value(row[4]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2012,
                                                                  population=_get_pollution_value(row[5]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2013,
                                                                  population=_get_pollution_value(row[6]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2014,
                                                                  population=_get_pollution_value(row[7]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2015,
                                                                  population=_get_pollution_value(row[8]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2016,
                                                                  population=_get_pollution_value(row[9]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2017,
                                                                  population=_get_pollution_value(row[10]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2018,
                                                                  population=_get_pollution_value(row[11]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)
                        record.save()
                        record = EurostatDataModel.objects.create(year=2019,
                                                                  population=_get_pollution_value(row[12]),
                                                                  nutsRegionStr=nutsRegionStr,
                                                                  nutsRegion=nutsRegion)

                        record.save()
        except Exception as e:
            print(e)
        logging.info("Loaded pollutants.")

    def load_dummy_data(self):
        """
        No implementation for EurostatDataSource.
        """
        pass



#######################
# SUPPORT FUNCTIONS
#######################


def _get_pollution_value(value: str) -> int:
    """
    Shortcut function for extracting number
    :param str: string which contains poppulation informatin
    :return: int value of population
    """
    number = 0
    array = [int(s) for s in value.split() if s.isdigit()]
    if len(array) != 0:
        number = array[0]

    return number
