"""
Author: Mark McDonald
This script includes models that support data
collected from pollution observation stations.
"""
import datetime
import logging

import pandas as pd
import pytz
from django.db import models
from django.db.models import Avg

from airpollution.models.models_nuts import NutsRegions, EUCountries, EU_ISOCODES
from airpollution.models.models_pollutants import Pollutant

model_logger = logging.getLogger("model_logger")
model_logger.setLevel(logging.ERROR)


class ObservationStation(models.Model):
    """
    Meta-Data for pollution observation stations
    """
    air_quality_station = models.CharField(max_length=48, primary_key=True)
    country_code = models.ForeignKey(EUCountries, on_delete=models.CASCADE, null=True, related_name="stations",
                                     db_index=True)
    air_quality_network = models.CharField(max_length=48)
    air_quality_station_eoicode = models.CharField(max_length=16, db_index=True)
    air_quality_station_natcode = models.CharField(max_length=16, db_index=True)
    projection = models.CharField(max_length=16)
    longitude = models.FloatField()
    latitude = models.FloatField()
    altitude = models.FloatField()
    nuts_1 = models.ForeignKey(NutsRegions, on_delete=models.CASCADE, related_name='nuts1_stations', null=True)
    nuts_2 = models.ForeignKey(NutsRegions, on_delete=models.CASCADE, related_name='nuts2_stations', null=True)
    nuts_3 = models.ForeignKey(NutsRegions, on_delete=models.CASCADE, related_name='nuts3_stations', null=True)
    air_quality_station_area = models.CharField(max_length=32)

    # @staticmethod
    # def get_geoframe(crs: int = None):
    #     gdf = gpd.GeoDataFrame()
    #
    #     qs = ObservationStation.objects.all()
    #
    #     for i, record in enumerate(qs):
    #         d = {'air_quality_station': record.air_quality_station,
    #              'country_code': record.country_code,
    #              'nuts_code': record.nuts_code,
    #              'air_quality_network': record.air_quality_network,
    #              'air_quality_station_eoicode': record.air_quality_station_eoicode,
    #              'air_quality_station_natcode': record.air_quality_station_natcode,
    #              'projection': record.projection,
    #              'longitude': record.longitude,
    #              'latitude': record.latitude,
    #              'altitude': record.altitude,
    #              'nuts_0': record.nuts_0,
    #              'nuts_1': record.nuts_1,
    #              'nuts_2': record.nuts_2,
    #              'nuts_3': record.nuts_3,
    #              'air_quality_station_area': record.air_quality_station_area}
    #
    #         gdf = gdf.append(gpd.GeoDataFrame(d, index=[i]))
    #
    #     # set the geometry and projection
    #     gdf = gpd.GeoDataFrame(gdf,
    #                            crs=crs if crs else record.projection,
    #                            geometry=gpd.points_from_xy(gdf.longitude, gdf.latitude))
    #
    #     return gdf

    @staticmethod
    def get_country_code(station: str) -> str:
        try:
            rs = ObservationStation.objects.get(pk=station)
        except Exception as e:
            return None

        return rs.country_code

    @staticmethod
    def get_stratified_stations(level: int = 1, n: int = 1, frac: float = None, countries: list = None) -> list:
        """
        Get a list of stations that are stratified based on the nuts level provided.
        Levels 0,1,2,3 return the number of following 26, 86, 219, 900, respectively.
        There are approximately 5000 stations in total.
        """

        # get the observation stations
        if countries is None or len(countries) == 0:
            rs = ObservationStation.objects.values()
        else:
            rs = ObservationStation.objects.filter(country_code__in=countries).values()

        # create a dictionary of the records
        rs_dict = {x['air_quality_station']: x for x in rs}

        # make it a dataframe
        df = pd.DataFrame(rs_dict).T

        # select 1 station from each nuts3 id
        nuts_levels = [df.country_code_id, df.nuts_1_id, df.nuts_2_id, df.nuts_3_id]
        nuts_level = nuts_levels[level]

        u_nuts = nuts_level.unique()

        station_ids = []
        for reg in u_nuts:
            _reg_df = df[nuts_level == reg].air_quality_station
            _max_n = len(_reg_df)
            _n = min(n, _max_n)

            if _max_n == 0:
                continue

            if frac is None:
                station_ids += _reg_df.sample(n=_n).values.tolist()
            else:
                # if the fraction yields 0 stations, take one
                _frac_df = _reg_df.sample(frac=frac)
                if len(_frac_df) == 0:
                    _frac_df = _reg_df.sample(n=_max_n)

                station_ids += _frac_df.values.tolist()

        return station_ids


class ObservationStationReading(models.Model):
    """
    Readings for EEA observation stations
    """
    key = models.CharField(max_length=128, primary_key=True)
    date_time = models.DateTimeField()
    country_code = models.ForeignKey(EUCountries, on_delete=models.CASCADE, null=True, related_name="observations")
    air_quality_network = models.CharField(max_length=48)
    air_quality_station = models.ForeignKey(ObservationStation, on_delete=models.CASCADE, blank=False)
    pollutant = models.ForeignKey(Pollutant, on_delete=models.DO_NOTHING, related_name="readings")
    value = models.FloatField()
    unit = models.CharField(max_length=16)
    validity = models.IntegerField()
    verification = models.IntegerField()

    @staticmethod
    def _get_rs_year_dayavg_by_country(country_code: str, year: int, logger: logging.Logger, pollutants: list = None):
        """
        Returns a recordset based on parameters from the ObservationStationReading model.
        If no pollutants are listed, all pollutants are returned.
        """

        if pollutants is None:
            pollutants = list(Pollutant.get_observation_pollutants().keys())

        try:
            c_obj = EUCountries.objects.get(pk=country_code.upper())
            rs = c_obj.observations.filter(date_time__year=year,
                                           validity=1,
                                           pollutant__in=map(str.upper, pollutants)).values('date_time__year',
                                                                                            'date_time__month',
                                                                                            'date_time__day',
                                                                                            'country_code',
                                                                                            'pollutant__key').annotate(
                Avg('value'))

        except Exception as e:
            logger.info(f"'{country_code.upper()}' is not an EU country.")
            return None

        if len(rs) == 0:
            logger.info(f"No records: {country_code.upper()} {year} {pollutants}")
            return None

        return rs

    @staticmethod
    def _get_rs_year_dayavg_by_countries(country_codes: list, year: int, logger: logging.Logger,
                                         pollutants: list = None):
        """
        Returns a recordset based on parameters from the ObservationStationReading model.
        If no pollutants are listed, all pollutants are returned.
        """

        if pollutants is None:
            pollutants = list(Pollutant.get_observation_pollutants().keys())
        try:
            rs = ObservationStationReading.objects.filter(country_code__in=country_codes,
                                                          date_time__year=year,
                                                          validity=1,
                                                          pollutant__in=map(str.upper, pollutants)).values(
                'date_time__year',
                'date_time__month',
                'date_time__day',
                'country_code',
                'pollutant__key') \
                .annotate(Avg('value'))

        except Exception as e:
            logger.info(f"'{country_codes}' is not an EU country.")
            return None

        if len(rs) == 0:
            logger.info(f"No records: {country_codes} {year} {pollutants}")
            return None

        return rs

    @staticmethod
    def _make_dataframe_bydayavg(rs, year_prefix, logger: logging.Logger) -> pd.DataFrame:
        """
        Creates a dataframe from a record set
        :param rs: Record set from the ObservationStationsReadings model
        :return: Dataframe
        """

        if rs is None or len(rs) == 0:
            return pd.DataFrame()

        r_list = [[datetime.datetime(year=r['date_time__year'],
                                     month=r['date_time__month'],
                                     day=r['date_time__day']), r['country_code'], r['pollutant__key'], r['value__avg']]
                  for r in rs]

        df = pd.DataFrame(r_list, columns=['date_time',
                                           'country_code',
                                           'pollutant__key',
                                           'value__avg']).sort_values(by='date_time').reset_index(drop=True)
        df['value__avg'] = pd.to_numeric(df['value__avg'])

        # split table into tables by pollutant
        p_list = df.pollutant__key.unique()
        df_list = []

        # for each data_frame calculate running statistics
        for p in p_list:
            d = df[df.pollutant__key == p].copy()
            d[f'{year_prefix}ytd-avg-level'] = pd.Series(d.value__avg.expanding().mean())
            df_list.append(d)

        rv_df = pd.concat(df_list)

        # add year_day
        rv_df['year_day'] = rv_df.apply(lambda s: s.date_time.timetuple().tm_yday, axis=1)

        return rv_df.rename(columns={'value__avg': f'{year_prefix}day-avg-level'}).sort_values(
            by=['pollutant__key', 'date_time'])

    @staticmethod
    def _combine_into_df(rs_PY, rs_CY, logger: logging.Logger) -> pd.DataFrame:

        df_PY = ObservationStationReading._make_dataframe_bydayavg(rs_PY, 'prior-', logger)
        df_CY = ObservationStationReading._make_dataframe_bydayavg(rs_CY, '', logger)

        if len(df_PY) == 0 and len(df_CY) > 0:
            df_CY = df_CY.rename(columns=({'date_time': 'date_time_CY'}))
            df_CY['prior-ytd-avg-level'] = pd.Series([0 for i in range(len(df_CY))])
            df_CY['prior-day-avg-level'] = pd.Series([0 for i in range(len(df_CY))])
            return df_CY

        if len(df_CY) == 0:
            return pd.DataFrame()

        if len(df_CY) == 0 and len(df_PY) == 0:
            return pd.DataFrame()

        return pd.merge(left=df_PY, right=df_CY, how='outer',
                        on=['country_code', 'pollutant__key', 'year_day'],
                        suffixes=('_PY', '_CY'))

    @staticmethod
    def _get_daily_df(country_code: str, current_year: int, pollutants: list, logger: logging.Logger) -> pd.DataFrame:
        """
        Returns daily averages and running averages for provided year and prior year.
        """
        rs_PY = ObservationStationReading._get_rs_year_dayavg_by_country(country_code, current_year - 1, logger,
                                                                         pollutants)
        rs_CY = ObservationStationReading._get_rs_year_dayavg_by_country(country_code, current_year, logger, pollutants)

        return ObservationStationReading._combine_into_df(rs_PY, rs_CY, logger)

    @staticmethod
    def _get_daily_countries_df(country_codes: list, current_year: int, pollutants: list,
                                logger: logging.Logger) -> pd.DataFrame:
        """
        Returns daily averages and running averages for provided year and prior year.
        """
        rs_PY = ObservationStationReading._get_rs_year_dayavg_by_countries(country_codes, current_year - 1, logger,
                                                                           pollutants)
        rs_CY = ObservationStationReading._get_rs_year_dayavg_by_countries(country_codes, current_year, logger,
                                                                           pollutants)

        return ObservationStationReading._combine_into_df(rs_PY, rs_CY, logger)

    @staticmethod
    def daily(start_date: str, end_date: str,
              countries: list = None, pollutants: list = None,
              logger: logging.Logger = model_logger) -> dict:
        """
                Returns the daily statistic of 'day-avg-level' and 'ytd-avg-level' for countries and pollutants
                provided in the argument lists.
                :param logger:
                :param start_date: YYYY-MM-DD string of start date
                :param end_date: YYYY-MM-DD string of end date
                :param countries: List of iso codes of countries
                :param pollutants: List of key string values of pollutants
                :return: Dictionary with daily statistics per pollutant per country
        """

        c_dict = {}
        s_year, s_month, s_day = [int(s) for s in start_date.split('-')]
        e_year, e_month, e_day = [int(s) for s in end_date.split('-')]

        # start_year and end_year must be the same year
        if s_year != e_year:
            return {'error': f'Can only produce results an range of dates within a single year. {s_year}-{e_year}'}

        if countries is None:
            countries = EU_ISOCODES

        if pollutants is None:
            pollutants = Pollutant.get_keys()

        df = ObservationStationReading._get_daily_countries_df(countries, e_year, pollutants, logger)

        for c in countries:
            c_df = df[df['country_code'] == c]
            if len(c_df) == 0:
                continue

            # filter for dates requested
            s_date = datetime.datetime(year=s_year, month=s_month, day=s_day)
            e_date = datetime.datetime(year=e_year, month=e_month, day=e_day)
            c_df = c_df[(c_df['date_time_CY'] >= s_date) & (c_df['date_time_CY'] <= e_date)]

            c_pollutants = c_df['pollutant__key'].unique()

            # get unique days for current year
            cy_dates = c_df['date_time_CY'].unique()

            d_dict = {}
            for cy_date in cy_dates:
                p_dict = {}
                day_df = c_df[c_df['date_time_CY'] == cy_date]

                for p in c_pollutants:
                    p_df = day_df[day_df['pollutant__key'] == p]

                    if len(p_df) == 0:
                        p_dict.update({p: {'day-avg-level': None,
                                           'ytd-avg-level': None,
                                           'prior-day_avg_level': None,
                                           'prior-ytd-avg-level': None}})
                    else:
                        p_df = p_df.iloc[0]
                        p_dict.update({p: {'day-avg-level': p_df['day-avg-level'],
                                           'ytd-avg-level': p_df['ytd-avg-level'],
                                           'prior-day_avg_level': p_df['prior-day-avg-level'],
                                           'prior-ytd-avg-level': p_df['prior-ytd-avg-level']}})
                d_dict.update({cy_date.astype(str).split('T')[0]: p_dict})

            c_dict.update({c: d_dict})

        return c_dict

    @staticmethod
    def get_pollutant_dayavg_by_station_df(date_from: str, date_to: str, pollutants: list):
        # parse dates
        s_year, s_month, s_day = [int(s) for s in date_from.split('-')]
        e_year, e_month, e_day = [int(s) for s in date_to.split('-')]

        tz = pytz.timezone("CET")
        date_from = datetime.datetime(year=s_year, month=s_month, day=s_day, tzinfo=tz)  # '2020-01-01'
        date_to = datetime.datetime(year=e_year, month=e_month, day=e_day, tzinfo=tz)  # '2020-04-30'

        readings_rs = ObservationStationReading.objects.filter(pollutant__key__in=pollutants).filter(
            date_time__gte=date_from,
            date_time__lte=date_to, validity=1).values(
            'air_quality_station_id',
            'pollutant_id').annotate(Avg('value'))
        readings_df = pd.DataFrame(readings_rs).rename(columns={'air_quality_station_id': 'air_quality_station'})
        return readings_df

    @staticmethod
    def annual(years: list = None, countries: list = None, pollutants: list = None,
               logger: logging.Logger = model_logger) -> dict:
        """
        Returns a dictionary of annual averages.
        :param years: Required. Years to include.  If year is not in DB, it is excluded from return value.
        :param countries: Optional. Countries to include.  Includes all EU countries if not provided. If country is missing from DB, it is excluded from response.
        :param pollutants: Optional. Pollutants to include.  Includes all pollutants if not provided. If pollutant is missing from DB, it is excluded from response.
        :param logger: Optional. Logger to display log results.
        :return: Dictionary of annual average of pollutants by country and year.
        """

        if countries is None:
            countries = EU_ISOCODES

        if pollutants is None:
            pollutants = list(Pollutant.get_observation_pollutants().keys())

        if years is None:
            years = []
            u_years_rs = ObservationStationReading.objects.filter(country_code__in=countries, validity=1,
                                                                  pollutant__in=map(str.upper, pollutants)).values(
                'date_time__year').distinct()
            for item in u_years_rs:
                years.append(list(item.values())[0])
        years.sort()

        # craete dataframe of all years
        df = pd.DataFrame()
        for year in years:
            try:
                rs = ObservationStationReading.objects.filter(country_code__in=countries,
                                                              date_time__year=year,
                                                              validity=1,
                                                              pollutant__in=map(str.upper, pollutants)).values(
                    'date_time__year',
                    'country_code',
                    'pollutant__key') \
                    .annotate(Avg('value'))

            except Exception as e:
                logger.info(f"{e}")
                continue

            if rs is None or len(rs) == 0:
                logger.info(f"No records in {year}")
                continue

            df = df.append(pd.DataFrame(rs))

        # create dictionary formatted per requirements
        rv_dict = {}
        u_countries = df.country_code.unique()
        for c in u_countries:
            u_years = df[df.country_code == c].date_time__year.unique()
            y_dict = {}

            for y in u_years:
                xx_df = df[(df.country_code == c) & (df.date_time__year == y)]
                y_dict.update({int(y): dict(zip(xx_df['pollutant__key'], xx_df['value__avg']))})
            rv_dict.update({c: y_dict})

        return rv_dict



