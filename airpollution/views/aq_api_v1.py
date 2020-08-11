# Air Quality API Gateway
"""
This module serves as an api for views and provides access to the application database.
The functions in this module may return data from numerous backend datasources.
This file will contain a series of Django routes.
Each route in this module will require a corresponding urlpattern entry in urls.py
These should return the dictionary values specified in
    https://docs.google.com/document/d/1saez6QW-cXMATwMG6F1O0RkZuXX-6IjMcW3dxkWLHgo/edit#

Responses
    OK                  request was successful
    INVALID_REQUEST     request was malformed
    OUT_OF_BOUNDS_TIME  dates are outside of the supported time range for that request
    REQUEST_DENIED      did not complete the request
    UNKNOWN_ERROR       unknown error

"""
import json
import logging

import geopandas as gpd
import numpy as np
import pandas as pd
from bokeh.models import GeoJSONDataSource
from django.http import JsonResponse

from airpollution.models import ObservationStationReading, ObservationStation, Pollutant, NutsRegions, \
    CURRENT_NUTS_VERSION, EEADataModel, EurostatDataModel


def _get_api_logger(name: str, verbosity: int = 0) -> logging.Logger:
    if verbosity > 2:
        verbosity = 2

    v_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
    logger = logging.getLogger(name=name)
    logger.setLevel(level=v_map.get(verbosity))

    return logger


def _get_annual_data(years: list, countries: list = None, pollutants: list = None, verbosity: int = 0) -> dict:
    logger = _get_api_logger("daily_logger", verbosity=verbosity)

    if type(countries) == str:
        countries = countries.replace(' ', '').split(',')
    if type(pollutants) == str:
        pollutants = pollutants.replace(' ', '').split(',')

    return ObservationStationReading.annual(years=years,
                                            countries=countries,
                                            pollutants=pollutants,
                                            logger=logger)


def annual(request, years:list=None, countries:list=None, pollutants:list=None, verbosity:int = 0) -> JsonResponse:
    """
    /aq_api/annual
    Provides pollutant levels in units of micro g/m3 by pollutant, country, and year.
    Note: This API method only provides annual data from [START DATE] through [END DATE]

    Provides pollutant levels in units of micro g/m3 by pollutant, country, and year.
    Example request:

    For all pollutants, all countries, all years:
    http://localhost:8000/aq_api/annual/?version=v1

    For a set of countries, pollutants and/or years:
    http://localhost:8000/aq_api/annual?version=v1&countries=de,fr,be&years=2016,2017,2018&pollutants=o3,co
    :param request:
    :return:
    """
    if request is not None:
        version = request.GET.get('version', None)
        if pollutants is None:
            pollutants = request.GET.get('pollutants', None)
        if countries is None:
            countries = request.GET.get('countries', None)
        if years is None:
            years = request.GET.get('years', None)
        if verbosity is None:
            verbosity = request.GET.get('verbosity', 0)

    results = _get_annual_data(years, countries, pollutants, verbosity=verbosity)

    return JsonResponse(results, safe=False)


def daily(request) -> JsonResponse:
    """
    /aq_api/daily
    Provides pollutant levels in units of micro g/m3 by region, pollutant, and date.
    Example request (not limited data in development envorinment):
    http://localhost:8000/aq_api/daily?version=v1&regions=de,fr,be&pollutants=no,o3,co&start-date=2020-01-01&end-date=2020-03-19

    Example to get all data available (gets all data in a development environment - will be large for production):
    http://localhost:8000/aq_api/daily?version=v1&start-date=2020-01-01&end-date=2020-12-31


    :param request:
    :return: Dictionary.
    """
    version = request.GET.get('version', '')
    countries = request.GET.get('regions', None)
    pollutants = request.GET.get('pollutants', None)
    start_date = request.GET.get('start-date', None)
    end_date = request.GET.get('end-date', None)
    verbosity = request.GET.get('verbosity', 0)

    if end_date is None and start_date is not None:
        end_date = start_date

    # TODO: Make this a 404 error
    if start_date is None or end_date is None:
        return JsonResponse("Both 'start-date' and 'end-date' are required parameters.", safe=False)

    results = get_daily_data(countries, pollutants, start_date, end_date, verbosity)

    return JsonResponse(results, safe=False)


def get_daily_data(countries, pollutants, start_date, end_date, verbosity: int = 0):
    logger = _get_api_logger("daily_logger", verbosity=verbosity)

    if type(countries) == str:
        countries = countries.replace(' ', '').split(',')
    if type(pollutants) == str:
        pollutants = pollutants.replace(' ', '').split(',')
    return ObservationStationReading.daily(start_date=start_date,
                                           end_date=end_date,
                                           countries=countries,
                                           pollutants=pollutants, logger=logger)


def _get_nuts2_population_series():
    # get nuts2 region population of most recent year
    df = pd.DataFrame(EurostatDataModel.objects.all().values('year', 'nutsRegionStr',
                                                             'population'))  # .drop(columns=['id', 'nutsRegion'])
    df = df.rename(columns={'nutsRegionStr': 'nuts_2_id'})
    df_pivot = df.pivot_table(columns=['year'], index=['nuts_2_id'])
    df_pivot.columns = df_pivot.columns.get_level_values(1)

    # get most recent year
    pop_year = df_pivot.columns[df_pivot.columns.argmax()]
    population = df_pivot[pop_year]
    population.name = 'population'

    return population


def get_target_bubblemap_data(start_date: str, end_date: str, pollutants: list = ('PM25', 'PM10', 'NO2')):
    # Create Data for Visualization

    # get daily average readings over date range for pollutant
    readings_df = ObservationStationReading.get_pollutant_dayavg_by_station_df(start_date, end_date, pollutants)

    # get all stations meta data
    rs_stations = ObservationStation.objects.all().values()
    stations_df = pd.DataFrame(rs_stations)

    # merge the readings with the meta data
    df = stations_df.merge(readings_df)

    def parse_nuts(s):
        return s.split('_')[-1]

    # get the nuts 2 region names
    df['nuts_1_id'] = df['nuts_1_id'].apply(parse_nuts)
    df['nuts_2_id'] = df['nuts_2_id'].apply(parse_nuts)
    df['nuts_3_id'] = df['nuts_3_id'].apply(parse_nuts)
    _n = 2
    nuts_boundaries = get_region_boundaries_data(level=None, regions=None)
    reg_df = pd.DataFrame(nuts_boundaries[_n]).T.reset_index().rename(
        columns={'name': f'nuts_{_n}_name', 'index': f'nuts_{_n}_id'})

    df = df.merge(reg_df, how='inner')

    # add targets to the measurements dataframe
    end_year = int(end_date[:4])
    t_df = Pollutant.get_targets_df(years=[end_year], pollutants=pollutants)
    t_df.rename(columns={'country': 'country_code_id', 'value': 'target_value'}, inplace=True)
    t_df = t_df[t_df['measurement_id'] == 'calendar_year']

    df = df.merge(t_df)

    # add target achievement
    df['achievement'] = (df['value__avg'] / df['target_value'])

    population = _get_nuts2_population_series()

    df = df.merge(population, left_on='nuts_2_id', right_on='nuts_2_id')

    df['radius'] = df['population'] / df['population'].max() * 50 + 10

    # create a GeoPandas Object to plot from
    rs_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    rv = {}
    for p in pollutants:
        p_gdf = rs_gdf[rs_gdf['pollutant_id'] == p]
        p_geo = GeoJSONDataSource(geojson=json.dumps(p_gdf.__geo_interface__))
        rv.update({p: p_geo})

    return rv


def get_target_data(years, regions, pollutants):
    # convert years, regions and pollutants to lists
    if type(regions) == str:
        regions = regions.split(',')
    if type(years) == str:
        years = [int(y) for y in years.split(',')]
    if type(pollutants) == str:
        pollutants = pollutants.split(',')

    return Pollutant.get_all_targets(years=years,
                                     country_codes=regions,
                                     pollutants=pollutants)


def region_boundaries(request) -> JsonResponse:
    """
    /aq_api/region-boundaries
    Returns NUTS region boundaries.
    :param level: Level for which to return boundaries for.  If None, all are returned.
    :param regions: List of countries for which to return boundaries for.  In None, all EU countries are returned.
    :param year: Year of the EU NUTS region version.
    :return: A dictionary with the boundaries.

    Provides a list bounding shapes for NUTS regions.

    Example request:
    For all regions:
    http://localhost:8000/aq_api/region_boundaries?version=v1

    For a set of regions
    http://localhost:8000/aq_api/region_boundaries?version=v1&regions=DE,FR
    :param request:
    :return:
    """
    version = request.GET.get('version', '')
    level = request.GET.get('level', 0)
    regions = request.GET.get('regions', None)
    year = request.GET.get('year', CURRENT_NUTS_VERSION)

    results = get_region_boundaries_data(level, regions, year)

    return JsonResponse(results, safe=False)


def get_region_boundaries_data(level, regions, year=CURRENT_NUTS_VERSION):
    # convert years, regions and pollutants to lists
    if type(level) == str:
        level = str(level)
    if type(regions) == str:
        regions = regions.split(',')
    if type(year) == str:
        year = int(year)
    return NutsRegions.get_nuts_region_boundaries(nuts_level=level,
                                                  country_codes=regions,
                                                  year=year)


# def region_info(request, nuts_level: int = None, year: int = CURRENT_NUTS_VERSION) -> JsonResponse:
def region_info(request) -> JsonResponse:
    """
    /aq_api/region-info
    Provides a list of NUTS regions and associated information.
    Returns a dictionary of NUTS regional details based on nuts_level provided.
    If nuts_level is None, all nuts levels are returned.
    :param request: Django request
    :param nuts_level: NUTS Level. Optional. If None, all levels are returned.
    :param year: Year of the version.  Optional. Current Nuts version is defaulted.
    :return: A JSON object with the nuts regions per level.
    Example request:

    For all regions:
    http://localhost:8000/aq_api/region_info?version=v1

    For a given level:
    http://localhost:8000/aq_api/region_info?version=v1&levels=0
    http://localhost:8000/aq_api/region_info?version=v1&levels=1
    :param request:
    :return:
    """
    version = request.GET.get('version', '')
    level = request.GET.get('levels', None)
    year = request.GET.get('year', CURRENT_NUTS_VERSION)

    results = get_region_info_data(level, year)

    return JsonResponse(results, safe=False)


def get_region_info_data(level, year=CURRENT_NUTS_VERSION):
    # convert years, regions and pollutants to lists
    if type(level) == str:
        level = int(level)
    if type(year) == str:
        year = int(year)
    results = NutsRegions.get_nuts_regions(nuts_level=level, year=year)
    return results


def sectors(request) -> JsonResponse:
    """
    /aq_api/sectors
    Provides emissions data by sector, pollutant, country, and year.
    Note: This API works for dates 1990 through 2017

    Example requests:
    For all pollutants, all countries, all sectors, and all years:
        http://localhost:8000/aq_api/sectors/?version=v1

    For a set of pollutants, countries, sectors, and/or years:
        http://localhost:8000/aq_api/sectors/?
        version=v1&
        countries=de,fr,be&
        years=2016,2017,2018&
        pollutants=o3,co&
        sectors=oil-gas-production          using dashes in the request won't work because some of the sectors have a dash in the data

    Working examples
        http://localhost:8000/aq_api/sectors?version=v1&countries=FR&years=2016,2017,2018&pollutants=CO
        http://localhost:8000/aq_api/sectors?version=v1&countries=FR&years=2016,2017,2018&pollutants=PM2.5
        http://localhost:8000/aq_api/sectors?version=v1&pollutants=PM2.5&sectors=Agriculture
        http://localhost:8000/aq_api/sectors?version=v1&pollutants=PM2.5&sectors=Road_transport
        http://localhost:8000/aq_api/sectors?version=v1&pollutants=PM2.5&sectors=Non-road_transport
        http://localhost:8000/aq_api/sectors?version=v1&sectors=Industrial_processes_and_product_use
        http://localhost:8000/aq_api/sectors?version=v1&sectors=Commercial,_institutional_and_households
        http://localhost:8000/aq_api/sectors?version=v1&sectors=Energy_production_and_distribution
        http://localhost:8000/aq_api/sectors?version=v1&countries=DK&sectors=Energy_production_and_distribution

    Currently multiple couuntries or pollutants doesn't work
    :param request:
    :return:
    """
    version = request.GET.get('version', '')
    countries = request.GET.get('countries', '')
    years = request.GET.get('years', '')
    pollutants = request.GET.get('pollutants', '')
    sects = request.GET.get('sectors', '')  # must be sects, 'sectors' in the function name

    sects = sects.replace("_", " ")

    # convert years, regions and pollutants to lists
    if type(countries) == str:
        countries = countries.split(',')
    if type(years) == str:
        years = [int(y) for y in years.split(',')]
    if type(pollutants) == str:
        pollutants = pollutants.split(',')
    if type(sects) == str:
        sects = sects.split(',')

    results = EEADataModel.get_sectors_info(year=years, country_code=countries, sector_group=sects,
                                            pollutant=pollutants)
    return JsonResponse(results, safe=False)


def targets(request) -> JsonResponse:
    """
    /aq_api/targets
    Provides a list of target emission levels by region, pollutant type, and year.
    Example request:

    For all pollutants, all regions, all years:
    http://localhost:8000/aq_api/targets?version=v1

    For a set of regions, pollutants and/or years:
    http://localhost:8000/aq_api/targets?version=v1&regions=de,fr,be&years=2016,2017,2018&pollutants=o3,co
    :param request:
    :return:
    """
    version = request.GET.get('version', '')
    regions = request.GET.get('regions', None)
    years = request.GET.get('years', None)
    pollutants = request.GET.get('pollutants', None)

    # TODO: Provide HTTP response
    if years is None:
        years = [y for y in range(2016, 2025)]
        # return JsonResponse("Years are required", safe=False)

    # convert years, regions and pollutants to lists
    if type(regions) == str:
        regions = regions.split(',')
    if type(years) == str:
        years = [int(y) for y in years.split(',')]
    if type(pollutants) == str:
        pollutants = pollutants.split(',')

    results = Pollutant.get_all_targets(years=years, country_codes=regions, pollutants=pollutants)

    return JsonResponse(results, safe=False)
