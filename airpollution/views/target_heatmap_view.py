import json
import numpy as np
import pandas as pd
import geopandas as gpd

from bokeh.models import HoverTool, WheelZoomTool, ResetTool, PanTool, Panel, Tabs
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, FixedTicker, NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.embed import json_item
from django.http import JsonResponse
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.palettes import RdYlGn11


from airpollution.models.models_copernicus import SatelliteImageFiles
from airpollution.models.models_pollutants import Target


def get_bounds(bottom_left_latlon: tuple = (-24.95, 30.05), top_right_latlon: tuple = (44.95, 69.95)):
    wgs84_bounds = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x=[bottom_left_latlon[0], top_right_latlon[0]],
                                                                y=[bottom_left_latlon[1], top_right_latlon[1]]), crs=4326)
    mercator_bounds = wgs84_bounds.to_crs('EPSG:3857')
    """
    Returns boundaries of a map through a bottom-left and top-right coordinate
    :param bottom_left_latlon: tuple of the bottom left coordinates of the clipping path
    :param top_right_latlon: tuple of the top right coordinates of the clipping path
    :param wgs84_bounds: A simple Geopandas object with a set of default lat long coordinates 
    :return: Returns the x and y range of a map
    """  

    bl = mercator_bounds.iloc[0].geometry.bounds[:2]
    tr = mercator_bounds.iloc[1].geometry.bounds[:2]

    # get x and y range of image_df
    x_range = (bl[0], tr[0])
    y_range = (bl[1], tr[1])

    return x_range, y_range


def _build_gdf_from_image(image, x_range, y_range, filter_val):
    """
    Returns a Geopandas data frame
    :param image: A 2-dimensional vector of pollution readings data
    :param x_range: the longitude range of the map to be generated
    :param y_range: the latitude range of the map to be generated
    :param filter_val: Readings that should be filtered out (eg types of pollutants)
    :return: A Geopandas object with specified readings filtered out
    """ 

    lats = np.linspace(y_range[0], y_range[1], image.shape[0])
    lons = np.linspace(x_range[0], x_range[1], image.shape[1])

    i_df = pd.DataFrame(image, columns=lons, index=lats[::-1])
    lats_list = np.array([i_df.index] * image.shape[1]).flatten()
    i_df = i_df.melt(value_vars=i_df.columns).set_index(lats_list).reset_index().rename \
        (columns={'index': 'latitude', 'variable': 'longitude'})
    i_gdf = gpd.GeoDataFrame(i_df, geometry=gpd.points_from_xy(i_df.longitude, i_df.latitude), crs=3857)

    i_gdf_filtered = i_gdf[i_gdf.value >= filter_val]

    return i_gdf_filtered


def draw_heatmap(request, plot_date: str = None, pollutants: list = ['PM25', 'PM10', 'NO2']):
    """

    :param request:
    :param plot_date:
    :param pollutants:
    :return:
    """

    if request is not None:
        pollutants = request.GET.get('pollutants', ['PM25', 'PM10', 'NO2'])
        plot_date = request.GET.get('plot_date', None)

    if plot_date is None:
        most_recent_date = SatelliteImageFiles.get_most_recent_date()
        year, month, day = most_recent_date.year, most_recent_date.month, most_recent_date.day
    else:
        year, month, day = (int(x) for x in plot_date.split('-'))

    # get images for the pollutants
    images = SatelliteImageFiles.get_dayavg_sat_images(pollutants=pollutants,
                                                       year=year, month=month, day=day,
                                                       category='ANALYSIS')

    if len(images) == 0:
        # if images for date not available - get the most recent date
        most_recent_date = SatelliteImageFiles.get_most_recent_date()
        year, month, day = most_recent_date.year, most_recent_date.month, most_recent_date.day
        # get images for the pollutants
        images = SatelliteImageFiles.get_dayavg_sat_images(pollutants=pollutants,
                                                           year=year, month=month, day=day,
                                                           category='ANALYSIS')

        if len(images) == 0:
            return JsonResponse(f"No images returned for selected date: {plot_date}", safe=False)

    # get targets
    targets = Target.objects.filter(pollutant__in=pollutants, measurement='calendar_year').values('pollutant_id',
                                                                                                  'value')
    targets = {x.get('pollutant_id'): x.get('value') for x in targets}

    # get figure boundaries
    x_range, y_range = get_bounds()

    # make images a +/- % of target overage
    for k, img in images.items():
        _i = (img / targets.get(k))
        images.update({k: _i})

    # max and min visible percentages
    min_val = .50
    max_val = 1.5

    # create bokeh elements
    tile_provider = get_provider(CARTODBPOSITRON)
    color_mapper = LinearColorMapper(palette=RdYlGn11, low=min_val, low_color='green', high=max_val, high_color='red')
    tick_format = NumeralTickFormatter(format='+0%')
    color_bar = ColorBar(color_mapper=color_mapper,
                         ticker=FixedTicker(ticks=[0, .25, 0.50, .75, 1, 1.25, 1.50]),
                         formatter=tick_format,
                         label_standoff=9, border_line_color=None, location=(0, 0))
    s_zoom = WheelZoomTool()
    s_pan = PanTool()
    s_reset = ResetTool()

    # setup tabs
    _tabs = []
    for _p in pollutants:
        # get dataframe from image
        i = images.get(_p)
        i_gdf_filtered = _build_gdf_from_image(i, x_range, y_range, min_val)

        # create geo source
        p_geo = GeoJSONDataSource(geojson=json.dumps(i_gdf_filtered.__geo_interface__))

        # create figure (canvas)
        p = figure(title=f'Satellite Image Average from {day}-{month}-{year} (>50% of target is shown in overlay)',
                   x_range=x_range, y_range=y_range,
                   sizing_mode='scale_both',
                   x_axis_type="mercator", y_axis_type="mercator",
                   x_axis_location=None,
                   y_axis_location=None,
                   tools=[s_zoom, s_pan, s_reset])
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        p.name = _p

        # add background map
        p.add_tile(tile_provider)

        # add heat map as points
        heatmap = p.circle(x='x', y='y', size=1.2, color={'field': 'value', 'transform': color_mapper}, alpha=.25,
                           source=p_geo)

        # add colorbar
        p.add_layout(color_bar, 'right')

        # add hover tool for stations
        hover_tool = HoverTool(renderers=[heatmap],
                               tooltips=[
                                   (f"+/-% of {p.name} target", "@value{:+%0.0}"),
                               ])
        p.add_tools(hover_tool)  # , s_zoom, s_pan, s_reset)

        # add as a tab in tabs list
        _tabs.append(Panel(child=p, title=p.name))

    # create tabs
    tabs = Tabs(tabs=_tabs)
    tabs.sizing_mode = 'scale_both'
    # jupyter notebook
    # return tabs

    # django
    item = json_item(tabs)
    # item['metadata'] = 'somemetadata'

    return JsonResponse(item)
