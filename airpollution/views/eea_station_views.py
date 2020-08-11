"""
Author: Mark McDonald
This module is intended to gather information on the EEA
pollution reporting stations.
"""
import datetime
import logging

from django.http import JsonResponse

from airpollution.models import ObservationStation, ObservationStationReading

logging.basicConfig(level=logging.INFO)


def get_stations(request, station_name: str = None) -> JsonResponse:
    """
    Returns a rendered map with a script and div object.
    :param request: requests which contains the nuts_level and countries to be filtered
    :param station_name: String of the station (defaults to None)
    :return: Returns a JSON response with readings from EEA pollution stations
    """
    if station_name:
        qs = ObservationStation.objects.filter(air_quality_station=station_name)
    else:
        qs = ObservationStation.objects.all()

    rv = {}
    for i, s in enumerate(qs):
        val = {
                'country_code': s.country_code,
                'air_quality_network': s.air_quality_network,
                'air_quality_station_eoicode': s.air_quality_station_eoicode,
                'air_quality_station_natcode': s.air_quality_station_natcode,
                'projection': s.projection,
                'longitude': s.longitude,
                'latitude': s.latitude,
                'altitude': s.altitude,
                'air_quality_station_area': s.air_quality_station_area
        }

        rv.update({s.air_quality_station: val})

    return JsonResponse(rv, safe=False)


def get_pollution_observations(start_date: int,
                               end_date: int,
                               time_type: str,
                               country_code: str,
                               nuts_region: str,
                               station_code: str,
                               pollutant: str) -> JsonResponse:
    """
    Return surface pollution readings from base stations.
    :param station_code:
    :param start_date: YYYYMMDD. Start date of the observations to return.
    :param end_date: YYYYMMDD. End date of the observations. (inclusive)
    :param time_type: 'hourly' | 'day_mean' | 'rolling'.
                    'hourly' - all available hours for the day
                    'day_mean' - a mean value for all available and valid hours for each day
                    'rolling' - An 8-hour rolling mean for the day. Each hour value provided is the mean of that hour and the previous 7.
    :param country_code: Optional.  2-digit country code.  If country_code and nuts_region are supplied, the nuts_region will take precidence.
    :param nuts_region: Optional. Nuts region.  All regions are supported. If country_code is also supplied, the NUTS region will take precidence.
    :param pollutant: Optional. pollutant code of pollutant.  If none, all are returned.
    :return: JSON dictionary of the results.
    """

    def parse_ymdh(dstr) -> tuple:
        y = f'{dstr[:4]}'
        m = f'{dstr[4:6]}'
        d = f'{dstr[6:8]}'
        h = f'{dstr[8:]}'

        if not h:
            h = 0

        return int(y), int(m), int(d), int(h)

    start_date = parse_ymdh(start_date)
    end_date = parse_ymdh(end_date)

    datetime.datetime(start_date[0], start_date[1], start_date[2], start_date[3])

    # build kwargs for query
    kwargs = {'date_time_gte': start_date,
              'date_time__lte': end_date}

    if country_code:
        kwargs.update({'country_code': country_code})
    if station_code:
        kwargs.update({'air_quality_station': station_code})
    if pollutant:
        kwargs.update({'pollutant': pollutant})

    qs = ObservationStationReading.objects.filter(**kwargs)

    return JsonResponse(qs)
