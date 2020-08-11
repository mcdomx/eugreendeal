import json
import geopandas as gpd
import shapely.wkt
from bokeh.embed import json_item
from bokeh.models import GeoJSONDataSource, LinearColorMapper, Panel, Tabs, BasicTicker, ContinuousTicker, PrintfTickFormatter, FixedTicker, NumeralTickFormatter, ColorBar, HoverTool, WheelZoomTool, ResetTool, PanTool
from bokeh.palettes import RdYlGn11
from bokeh.plotting import figure
from django.http import JsonResponse
from shapely.geometry import Polygon

from airpollution.views.aq_api_v1 import get_daily_data, get_region_boundaries_data


def draw_map(request):
    """
    Returns a rendered map with a script and div object.
    :param request: Django request
    :param nuts_level: The nuts level for which to display the map
    :param countries: The country code of the regions to be mapped (eg: de, nl, fr)
    :param pollutants: The pollutants to be mapped (eg: o3, co)
    :param start_date: The start_date to be mapped (eg: o3, co)
    :return: Returns a rendered map with a script and div object.
    """
    # Read in paramters and set default values when no parameter is provided
    nuts_level = request.GET.get('nuts_level', '0')
    countries = request.GET.get('countries', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    if start_date is None:
        return JsonResponse("'start_date' is a required parameter.", safe=False)

    if end_date is None:
        end_date = start_date

    daily_levels = get_daily_data(countries=countries, pollutants=None, start_date=start_date, end_date=end_date)

    # Uncomment this to use dummy data for testing
    """
    import os
    from eugreendeal.settings import MEDIA_ROOT
    json_dir = os.path.join(MEDIA_ROOT, "media", "mock_api_payloads")
    with open(json_dir + "/daily.json") as f:
        daily_levels = json.load(f)
    """

    daily_df = gpd.GeoDataFrame()

    for region_key, region_value in daily_levels.items():
        for date_key, date_value in region_value.items():
            for pollutant_key, pollutant_value in date_value.items():

                if pollutant_value is None:
                    continue

                day = pollutant_value.get("day-avg-level", 0)
                if day is None:
                    day = 0

                dictionary = {
                    "nuts_id": region_key.upper(),
                    "date": date_key,
                    "pollutant": pollutant_key.upper(),
                    "pollutant_level": round(day, 2)
                }

                daily_df = daily_df.append(dictionary, ignore_index=True)

    if len(daily_df) > 0:
        # Aggregate daily pollutant data over date range
        daily_df = daily_df.groupby(["nuts_id", 'pollutant']).mean().reset_index()

        nuts_boundaries = get_region_boundaries_data(level=nuts_level, regions=countries)
        df = gpd.GeoDataFrame()

        level = nuts_boundaries.get(str(nuts_level))
        for key, record in level.items():
            dictionary = {
                "nuts_id": key.upper(),
                "name": record["name"],
                "country": record["country_code"].upper(),
                "geometry": gpd.GeoSeries(shapely.wkt.loads(record["geography"]))}

            df = df.append(gpd.GeoDataFrame(dictionary), ignore_index=True)

        df.crs = 4326

        # Merge NUTS data frame with daily pollutant level dataframe
        df = df.merge(daily_df)
        
        #Reverse the list order of the spectrum since all the online tools put them in the oppposite order to what we want
        colors = ["#a50026", "#d3322b", "#f16d43", "#fcab63", "#fedc8c", "#f9f7ae", "#d7ee8e", "#a4d86f", "#64bc61"][::-1] 

        # Define the bounds of the EU's main territories (excluding far off islands)
        eu_bounds = Polygon([(-25, 35), (33, 35), (33, 70), (-25, 70), (-25, 35)])

        # Unique pollutants in df
        unique_pollutants = df.pollutant.unique()

        # create bokeh elements
        tabs_list = []
        for pollutant in unique_pollutants:
            
            filtered_df = df[df.pollutant.eq(pollutant)]
            
            # get unique areas base on the region type selected
            pollution_values = filtered_df['pollutant_level']
            min_pollution_value = pollution_values.min()
            max_pollution_value = pollution_values.max()

            color_mapper = LinearColorMapper(palette=RdYlGn11, low=min_pollution_value, low_color='green', high=max_pollution_value, high_color='red')
            tick_format = NumeralTickFormatter(format='0.0')

            color_bar = ColorBar(color_mapper=color_mapper,
                            #ticker=FixedTicker(ticks=[min_pollution_value, 2.7, max_pollution_value - min_pollution_value, max_pollution_value]),
                            ticker=BasicTicker(desired_num_ticks=len(colors)),
                            formatter=tick_format,
                            major_label_text_font_size="7px",
                            location=(0, 0))

            tools = [HoverTool(
                tooltips=[
                    ("Latitude, Longitude", "$x{0.000}, $y{0.000}"),
                    ("Country", "@country"),
                    ("NUTS ID", "@nuts_id"),
                    ("Avg " + pollutant + " level", "@pollutant_level{0.0}")
                ]
            ), WheelZoomTool(), PanTool(), ResetTool()]
        
            # Clip the polygons to the EU bounds
            filtered_df = gpd.clip(filtered_df, eu_bounds)

            bokeh_figure = figure(title="Air quality by region",
                                sizing_mode='scale_both',
                                tools=tools,
                                toolbar_location = None,
                                x_axis_location=None,
                                y_axis_location=None,
                                match_aspect=True,
                                border_fill_color=None
                                )
            
            bokeh_figure.xgrid.grid_line_color = None
            bokeh_figure.ygrid.grid_line_color = None

            geo_json_data_source = GeoJSONDataSource(geojson=json.dumps(filtered_df.__geo_interface__))
            # don't use a line color. the map consists of numerous patches, so you will only see the line color
            bokeh_figure.patches(xs="xs", ys="ys",
                                source=geo_json_data_source,
                                fill_color={"field": "pollutant_level", "transform": color_mapper},
                                line_color=None
                                )
            
            bokeh_figure.name = pollutant

            
            # add colorbar
            if(df.nuts_id.nunique() > 1): 
                bokeh_figure.add_layout(color_bar, 'right')
            
            tabs_list.append(Panel(child=bokeh_figure, title=bokeh_figure.name))

        tabs = Tabs(tabs=tabs_list)
        tabs.sizing_mode = 'scale_both'

        # script, div = components(bokeh_figure)
        item = json_item(tabs)
        # return render(request, 'airpollution/test-maps.html', dict(script=script, div=div))
        return JsonResponse(item)

    else:
        nuts_boundaries = get_region_boundaries_data(level=nuts_level, regions=countries)
        df = gpd.GeoDataFrame()

        level = nuts_boundaries.get(str(nuts_level))
        for key, record in level.items():
            dictionary = {
                "nuts_id": key.upper(),
                "name": record["name"],
                "country": record["country_code"].upper(),
                "geometry": gpd.GeoSeries(shapely.wkt.loads(record["geography"]))}

            df = df.append(gpd.GeoDataFrame(dictionary), ignore_index=True)

        df.crs = 4326
        
        #Filter down to a pretty set of countries as background
        blank_countries = ["NL", "BE", "LU", "FR", "DE"]
        df = df[df.nuts_id.isin(blank_countries)]
        
        # Define the bounds of the EU's main territories (excluding far off islands)
        eu_bounds = Polygon([(-25, 35), (33, 35), (33, 70), (-25, 70), (-25, 35)])
    
        # Clip the polygons to the EU bounds
        filtered_df = gpd.clip(df, eu_bounds)

        bokeh_figure = figure(title="No air quality data for the selected dates",
                            sizing_mode='scale_both',
                            toolbar_location = None,
                            x_axis_location=None,
                            y_axis_location=None,
                            match_aspect=True,
                            border_fill_color=None
                            )
        
        bokeh_figure.xgrid.grid_line_color = None
        bokeh_figure.ygrid.grid_line_color = None

        geo_json_data_source = GeoJSONDataSource(geojson=json.dumps(filtered_df.__geo_interface__))
        # don't use a line color. the map consists of numerous patches, so you will only see the line color
        bokeh_figure.patches(xs="xs", ys="ys",
                            source=geo_json_data_source,
                            line_color=None,
                            fill_color="#D3D3D3"
                            )
    
        # script, div = components(bokeh_figure)
        item = json_item(bokeh_figure)
        # return render(request, 'airpollution/test-maps.html', dict(script=script, div=div))
        return JsonResponse(item)

