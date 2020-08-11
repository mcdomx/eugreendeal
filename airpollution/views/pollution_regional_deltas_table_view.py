import json
import json
import os
import urllib.request

import pandas as pd
import shapely.wkt
from bokeh.embed import components, json_item
from bokeh.models import ColumnDataSource
from bokeh.layouts import widgetbox
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
from django.http import JsonResponse
import random

from airpollution.views.aq_api_v1 import get_daily_data, get_region_info_data


def draw_plot(request):
    """
    Returns a rendered map with a script and div object.
    :param request: requests which contains the nuts_level and countries to be filtered
    :return: Returns a rendered map with a script and div object.
    """
    # Read in paramters and set default values when no parameter is provided
    nuts_level = request.GET.get('nuts_level', '0')
    countries = request.GET.get('countries', None)
    
    #Removed pollutant filtering from this view. Set variable below to a request value if you'd like to filter on pollutants
    pollutant = None
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    #Get daily pollution levels fom the air quality API
    #This data can also be requested using via REST requests (eg http://localhost:8000/aq_api/daily?nuts_level=0&countries=BU&start-date=2020-03-01&end-date=2020-03-31)
    try:
        daily_levels = get_daily_data(countries, pollutant, start_date, end_date)
    except:
        print("Malformed request to the air quality API")


    #Create blank dataframe to be filled with JSON response values
    daily_df = pd.DataFrame()

    for region_key, region_value in daily_levels.items():
        for date_key, date_value in region_value.items():
            for pollutant_key, pollutant_value in date_value.items():
                if pollutant_value is None:
                    continue

                day = pollutant_value.get("day-avg-level", 0)
                yoy = pollutant_value.get("prior-day_avg_level", 0)
                if day is None:
                    day = 0
                if yoy is None:
                    yoy = 0

                dictionary = {
                    "nuts_id": region_key.upper(),
                    "date": date_key,
                    "pollutant": pollutant_key.upper(),
                    "pollutant_level": round(day, 2),
                    "yoy_level": round(yoy, 2)
                }

                daily_df = daily_df.append(dictionary, ignore_index=True)

    if len(daily_df) > 0:
        # Aggregate daily pollutant data over date range
        table_df = daily_df.groupby(["pollutant", "nuts_id"]).mean().reset_index()
        
        # Calculate year-over-year data and display it as a percentage
        table_df['yoy_change'] = 100 * ((table_df["pollutant_level"] / table_df["yoy_level"]) - 1)
        
        #Cast to string to display correct decimal point
        table_df["pollutant_level"] = round(table_df["pollutant_level"], 2).astype(str)
        table_df["yoy_change"] = round(table_df["yoy_change"], 2).astype(str)

        # format +/- percentages
        # Add positive symbol to make it clear that pollution has increased
        def df_format(s):
            x = s['yoy_change']
            pm = '' if x[0] == '-' else '+'
            rv = pm + x + '%'
            return rv

        table_df['yoy_change'] = table_df.apply(df_format, axis=1)

        regional_info = get_region_info_data(nuts_level)

        #Create blank dataframe to be filled with JSON response values
        region_df = pd.DataFrame()
        
        level = regional_info.get(int(nuts_level))
        for key, record in level.items():
            dictionary = {
                "nuts_id": key.upper(),
                "name": record["name"]
                }

            region_df = region_df.append(dictionary, ignore_index=True)
        
        # Merge region info data to get the region name
        df = table_df.merge(region_df)

    else:
            print("#No values available for given date range. Rendering empty table")
            df = pd.DataFrame(columns=['nuts_id','name','pollutant','pollutant_level','yoy_change'])
            df.loc[len(df)] = ['No data for date range','-','-','-','-']
    
    # Convert pandas dataframe into Bokeh's native column data format
    source = ColumnDataSource(df)
    
    columns = [
            TableColumn(field="nuts_id", title="Region Code"),
            TableColumn(field="name", title="Region Name"),
            TableColumn(field="pollutant", title="Pollutant"),
            TableColumn(field="pollutant_level", title="Current Level"),
            TableColumn(field="yoy_change", title="Year-Over-Year Change")
        ]
    data_table = DataTable(source=source, columns=columns, sizing_mode='stretch_width', index_position=None)

    # script, div = components(bokeh_figure)
    item = json_item(data_table)
    
    # return render(request, 'airpollution/time-series.html', dict(script=script, div=div))
    return JsonResponse(item)
