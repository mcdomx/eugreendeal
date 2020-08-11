import json
import logging

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.wkt
from bokeh.embed import components, json_item
from bokeh.models import GeoJSONDataSource, CategoricalColorMapper, Panel, Tabs, LinearColorMapper, \
    NumeralTickFormatter, ColorBar, FixedTicker, Label
from bokeh.models import HoverTool, WheelZoomTool, ResetTool, PanTool
from bokeh.palettes import RdYlGn11
from bokeh.plotting import figure
from django.http import JsonResponse
from django.shortcuts import render
from shapely.geometry import Polygon

from airpollution.models import NutsRegions
from airpollution.views.aq_api_v1 import get_target_bubblemap_data


class MapData:
    def __init__(self, crs: int = 4326):
        self.crs = crs
        self.df = None
        minx = -24.95
        miny = 30.05
        maxx = 44.95
        maxy = 71.95
        self.eu_bounds = Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)])
        self.aspect_ratio = ((maxx-minx)/(maxy-miny))*.8

    def _get_geoframe(self) -> gpd.GeoDataFrame:
        """
        Return GeoDataFrame object based on crs.
        :return: GeoPandas GeoDataFrame
        """
        if self.df is None:
            df = gpd.GeoDataFrame()

            qs = NutsRegions.objects.all()

            for record in qs:
                d = {'key': record.key,
                     'year': record.year,
                     'id': record.id,
                     'LEVL_CODE': record.LEVL_CODE,
                     'NUTS_ID': record.NUTS_ID,
                     'CNTR_CODE': record.CNTR_CODE,
                     'NUTS_NAME': record.NUTS_NAME,
                     'FID': record.FID,
                     # adding buffer(0) will correct any self-overlapping objects
                     'geometry': gpd.GeoSeries(shapely.wkt.loads(record.geometry).buffer(0))}

                df = df.append(gpd.GeoDataFrame(d), ignore_index=True)

            df.crs = self.crs  # set the projection

            df = self._crop_map(df)
            self.df = df

        return self.df

    # @staticmethod
    def _crop_map(self, df, minx=-24.95, miny=30.05, maxx=44.95, maxy=71.95) -> pd.DataFrame:
        """
        Will crop a geopandas dataframe to the area defined by the x and y boundaries provided.
        :param df:
        :param minx: Minimum longitude
        :param miny: Minimum latitude
        :param maxx: Maximum longitude
        :param maxy: Maximum latitude
        :return: A cropped Geopandas dataframe
        """
        # eu_bounds = Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)])

        return gpd.clip(df, self.eu_bounds)

    @staticmethod
    def get_geosource(df: gpd.GeoDataFrame) -> GeoJSONDataSource:
        """
        Convert dataframe to geojson. Define Bokeh datasource as GeoJson.
        :param df: dataframe to convert to geo source
        :return: GeoJSONDataSource
        """
        return GeoJSONDataSource(geojson=json.dumps(df.__geo_interface__))

    @staticmethod
    def get_bokeh_tools() -> list:
        """
        Return the default tools for Bokeh maps
        :return: list of tools to be displayed with map
        """
        tools = [
                    HoverTool(tooltips=[("index", "$index"),
                                        ("(lat,lon)", "($x{0.000}, $y{0.000})"),
                                        ("Country", "@CNTR_CODE"),
                                        ("key", "@key"), ])
                    , WheelZoomTool()
                    , PanTool()
                    , ResetTool()
                ]

        return tools

    def get_color_mapper(self) -> CategoricalColorMapper:
        """
        Return a Categorial color mapper that will map a color to specified nuts region level.
        :return: Categorical color mapper
        """
        df = self._get_geoframe()

        # get unique areas base on the region type selected
        regions = np.unique(df['NUTS_ID'])

        # assign color to each area (https://colorbrewer2.org/)
        colors = ['#b2182b', '#d6604d', '#f4a582', '#fddbc7', '#f7f7f7', '#d1e5f0', '#92c5de', '#4393c3', '#2166ac']
        colors = [colors[i % (len(colors))] for i in range(len(regions))]

        return CategoricalColorMapper(palette=colors, factors=regions)

    def get_bokeh_figure(self, height: int, width: int, include_tools):
        """
        Return a Bokeh figure with specified height and width
        :param include_tools:
        :param tools: Tools to include in the figure (_get_bokeh_tools())
        :param height: Height of the figure
        :param width: Width of the figure
        :return: Bokeh figure object
        """
        tools = []
        if include_tools:
            tools = self.get_bokeh_tools()

        p = figure(  # title='NUTS REGIONS',
                    # aspect_ratio=self.aspect_ratio,
                    # plot_height=height,
                    # plot_width=width,
                    # frame_height=height,
                    # frame_width=width,
                    sizing_mode='scale_both',
                    tools=tools,
                    x_axis_location=None,
                    y_axis_location=None)

        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        return p

    def get_map_df(self, nuts_level: int) -> gpd.GeoDataFrame:

        df = self._get_geoframe()

        rv = df[df['LEVL_CODE'] == nuts_level]

        if len(rv) < 2:
            logging.info(f"WARNING: filtered map has no points for NUTS level: {nuts_level}")
        return rv

    def get_maps_script_and_div(self, nuts_level: int = 0, height: int = 600, width: int = 600, include_tools=True):

        # restrict df to nuts region
        df = self.get_map_df(nuts_level)

        # make geosource based on new level
        geo_source = self.get_geosource(df)

        # get a color mapper
        color_mapper = self.get_color_mapper()

        # get a base figure
        p = self.get_bokeh_figure(height=height, width=width, include_tools=include_tools)

        # don't use a line color. the map consists of numerous patches, so you will only see the line color
        p.patches(xs='xs', ys='ys',
                  source=geo_source,
                  fill_color={'field': 'NUTS_ID', 'transform': color_mapper},
                  line_color=None)

        # using jupyter
        # return p

        # using Django
        script, div = components(p)

        return script, div


# Global MatData Object - avoids reloading data for multiple calls to get_nuts_map()
_md = MapData()


def get_nuts_map(nuts_level, height: int = 600, width: int = 600, outline_map=False, include_tools=True, exclude_countries:list = None):
    """
    Returns a rendered map with a script and div object.
    :param include_tools:
    :param outline_map:
    :param height:
    :param width:
    :param request: Django request
    :param nuts_level: The nuts level for which to display the map
    :return: Returns a rendered map with a script and div object.
    """

    # restrict df to nuts region
    df = _md.get_map_df(nuts_level)

    # filter out countries
    if exclude_countries is None:
        exclude_countries = []
    df = df[~df.CNTR_CODE.isin(exclude_countries)]

    # make geosource based on new level
    geo_source = _md.get_geosource(df)

    # get a color mapper
    if outline_map:
        fill_color = 'gainsboro'
        line_color = 'gray'
    else:
        color_mapper = _md.get_color_mapper()
        fill_color = {'field': 'NUTS_ID', 'transform': color_mapper}
        line_color = None

    # get a base figure
    p = _md.get_bokeh_figure(height=height, width=width, include_tools=include_tools)

    # don't use a line color. the map consists of numerous patches, so you will only see the line color
    p.patches(xs='xs', ys='ys',
              source=geo_source,
              fill_color=fill_color,
              line_color=line_color)

    # using jupyter
    # return p

    # using Django
    # script, div = components(p)

    # return render(request, 'airpollution/test-maps.html', dict(script=script, div=div))
    return p


def get_nuts_map_view(request, nuts_level, height: int = 600, width: int = 600):
    # script, div = get_nuts_map(0, height, width)
    # return render(request, 'airpollution/test-maps.html', dict(script=script, div=div))
    return render(request, 'airpollution/test-maps.html')


def get_nuts_map_data(request):
    p0 = get_nuts_map(0)
    p1 = get_nuts_map(1)
    p2 = get_nuts_map(2)
    tab0 = Panel(child=p0, title="NUTS1")
    tab1 = Panel(child=p1, title="NUTS2")
    tab2 = Panel(child=p2, title="NUTS3")
    tabs = Tabs(tabs=[tab0, tab1, tab2])
    tabs.sizing_mode = 'scale_both'

    item = json_item(tabs)
    item['metadata'] = 'somemetadata'
    response = JsonResponse(item)
    return response


def draw_bubble_map(request, start_date: str = None, end_date: str = None, pollutants: list = None):
    if request is not None:
        pollutants = request.GET.get('pollutants', ['PM25', 'PM10', 'NO2'])
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)

        if start_date is None:
            return JsonResponse("'start_date' is a required parameter.", safe=False)

        if end_date is None:
            end_date = start_date

    bubble_data = get_target_bubblemap_data(start_date=start_date, end_date=end_date, pollutants=pollutants)

    # create bokeh elements
    _tabs = []
    for k, v in bubble_data.items():
        p = get_nuts_map(0, outline_map=True, include_tools=False, exclude_countries=['TR'])

        p.name = k
        # add annotation
        top = p.properties_with_values().get('plot_height')
        note1 = Label(x=10, y=50, x_units='screen', y_units='screen',
                      text='NOTE: bubble size denotes Nuts2 Population.', render_mode='canvas',
                      border_line_color=None, border_line_alpha=1.0, text_alpha=.5, text_font_size='12px',
                      background_fill_color=None, background_fill_alpha=0.5)
        note2 = Label(x=10, y=30, x_units='screen', y_units='screen',
                      text='NOTE: color denotes percentage of target.', render_mode='canvas',
                      border_line_color=None, border_line_alpha=1.0, text_alpha=0.5, text_font_size='12px',
                      background_fill_color=None, background_fill_alpha=0.5)
        p.add_layout(note1)
        p.add_layout(note2)
        _tabs.append(Panel(child=p, title=p.name))

    tabs = Tabs(tabs=_tabs)
    tabs.sizing_mode = 'scale_both'

    color_mapper = LinearColorMapper(palette=RdYlGn11, low=.5, low_color='green', high=1.5, high_color='red')
    tick_format = NumeralTickFormatter(format='+0%')
    color_bar = ColorBar(color_mapper=color_mapper,
                         ticker=FixedTicker(ticks=[0, .25, 0.50, .75, 1, 1.25, 1.50]),
                         formatter=tick_format,
                         label_standoff=9, border_line_color=None, location=(0, 0))

    s_zoom = WheelZoomTool()
    s_pan = PanTool()
    s_reset = ResetTool()

    # create the bubbles and hover elements
    for t in tabs.tabs:
        # add colorbar
        t.child.add_layout(color_bar, 'right')

        # add bubbles
        glyphs = t.child.scatter(x='x', y='y', size='radius', source=bubble_data.get(t.child.name),
                                 fill_alpha=0.6, fill_color={'field': 'achievement', 'transform': color_mapper},
                                 line_color=None)

        # add hover tool for stations
        hover_tool = HoverTool(renderers=[glyphs],
                               tooltips=[("air_quality_station", "@air_quality_station"),
                                         ("Country", "@country_code_id"),
                                         ("NUTS 2", "@nuts_2_name"),
                                         ("NUTS 2 Pop", "@population"),
                                         (f"{t.child.name} Target Value", "@target_value"),
                                         ("Avg Value", "@value__avg"),
                                         ("% of Target", "@achievement{:+%0.0}")])
        t.child.add_tools(hover_tool, s_zoom, s_pan, s_reset)

    # jupyter notebook
    # return tabs

    # django
    item = json_item(tabs)
    # item['metadata'] = 'somemetadata'

    return JsonResponse(item)
