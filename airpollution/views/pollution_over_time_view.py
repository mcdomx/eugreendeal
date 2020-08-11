import pandas as pd
from bokeh.embed import json_item
from bokeh.models import Text, Line, ColumnDataSource, DatetimeTickFormatter, HoverTool, Legend, LegendItem
from bokeh.plotting import figure
from django.http import JsonResponse
from pygam import LinearGAM, s

from airpollution.views.aq_api_v1 import get_daily_data
from airpollution.views.aq_api_v1 import get_target_data

def draw_plot(request):
    """
    Returns a rendered map with a script and div object.
    :param request: Django request
    :return: Returns a JSON Bokeh object to be rendered in an html view
    """

    # Read in paramters and set default values when no parameter is provided
    nuts_level = request.GET.get("nuts_level", "0")
    countries = request.GET.get("countries", None)
    pollutant = request.GET.get("pollutant", None)
    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)
    smoothing = request.GET.get("smoothing", True)
    smooth_factor = request.GET.get("smooth_factor", 0.0) # values from 0-5.0 are reasonable

    # Define what will be seen in the hover tooltip
    tools = [HoverTool(
        tooltips=[
            ("Level", "$y{0.0}"),
            ("Date", '@date{%F}')
        ],
        formatters={'@date': 'datetime'}
    )]

    #Define the blank canvas of the Bokeh plot that data will be layered on top of
    bokeh_figure = figure(sizing_mode="scale_both",
                        height=300,
                        width=400,
                        tools=tools,
                        toolbar_location=None,
                        x_axis_type="datetime",
                        border_fill_color=None,
                        min_border_left=0)

    #Remove classic x and y ticks and chart junk to make things clean
    bokeh_figure.xgrid.grid_line_color = None
    bokeh_figure.xaxis.axis_line_color = None
    bokeh_figure.yaxis.axis_line_color = None
    bokeh_figure.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    bokeh_figure.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    bokeh_figure.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    bokeh_figure.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

    #Hide hours and minutes in the x-axis
    bokeh_figure.xaxis.formatter=DatetimeTickFormatter(days="%m/%d",
                                                        months="%m/%d",
                                                        hours="",
                                                        minutes="")

    #get target levels for the pollutant
    pollutant_targets = get_target_data(end_date[:-6], countries, pollutant)

    #Create blank dataframe to be filled with JSON response values
    targets_df = pd.DataFrame()

    for region_key, region_value in pollutant_targets.items():
        for year_key, year_value in region_value.items():
            for pollutant_key, pollutant_value in year_value.items():
                year_targets = pollutant_value.get("calendar_year", None)
                if year_targets is not None:
                    dictionary = {
                        "nuts_id": region_key.upper(),
                        "target": round(year_targets.get("value", 0), 2)
                    }

                    targets_df = targets_df.append(dictionary, ignore_index=True)

    #Get daily pollution levels fom the air quality API
    #This data can also be requested using via REST requests: (eg http://localhost:8000/aq_api/daily?nuts_level=0&countries=BU&start-date=2020-03-01&end-date=2020-03-31)
    try:
        daily_levels = get_daily_data(countries, pollutant, start_date, end_date)
        daily_api_sucess = True

        #If there are no nested items within the JSON payload, set it to false
        if (sum(map(len, daily_levels.values())) == 0):
            daily_api_sucess = False
            print("ERROR: No data available for specified pollutant")
    except:
        daily_api_sucess = False
        print("ERROR: The Air Quality API request failed")

    #Create blank dataframe to be filled with JSON response values
    daily_df = pd.DataFrame()

    if daily_api_sucess:

        for region_key, region_value in daily_levels.items():
            for date_key, date_value in region_value.items():
                for pollutant_key, pollutant_value in date_value.items():

                    dal = pollutant_value.get("day-avg-level", 0)
                    yoy = pollutant_value.get("prior-day_avg_level", 0)
                    if dal is None:
                        dal = 0
                    if yoy is None:
                        yoy = 0

                    dictionary = {
                        "nuts_id": region_key.upper(),
                        "date": date_key,
                        "pollutant": pollutant_key.upper(),
                        "pollutant_level": round(dal, 2),
                        "yoy_level": round(yoy, 2)
                    }

                    daily_df = daily_df.append(dictionary, ignore_index=True)

        if len(targets_df) > 0:
            daily_df = daily_df.merge(targets_df)

        # Aggregate daily pollutant data over date range
        time_series_df = daily_df.groupby(["date"]).mean().reset_index()
        time_series_df['date'] = pd.to_datetime(time_series_df['date'])
        time_series_df = time_series_df.fillna(0)

        # if smoothing argument is True, use a GAM to smooth plotted lines
        if smoothing:
            X = [x for x in time_series_df.index]
            time_series_df['pollutant_level'] = LinearGAM(s(0, lam=smooth_factor)).fit(X, time_series_df.pollutant_level).predict(X)
            time_series_df['yoy_level'] = LinearGAM(s(0, lam=smooth_factor)).fit(X, time_series_df.yoy_level).predict(X)

        # Convert pandas dataframe into Bokeh's native column data format
        source = ColumnDataSource(time_series_df)
        
        #Assign color to each pollutant
        colors = {
            "SO2": "#EA2F83", #pink
            "CO": "#FFB500", #yellow
            "PM25": "#4CAF50", #green
            "O3" : "#F2703B", #orange
            "NO" : "#0597D5", #blue
            "NO2" : "#0597D5", #blue
            "PM10" : "#7FD956" #light-green
        }
        
        #Create a glyph to be layered on top of the Bokeh figure (glyphs can contain one line or more)
        glyph = Line(x="date", y="pollutant_level", line_color=colors.get(pollutant), line_width=3, line_alpha=1)
        glyph_yoy = Line(x="date", y="yoy_level", line_color= colors.get(pollutant), line_width=3, line_alpha=0.3)

        #Add glyph to the Bokeh canvas
        bokeh_figure.add_glyph(source, glyph)
        bokeh_figure.add_glyph(source, glyph_yoy)

        #Add legend for line glyphs on plot
        li1 = LegendItem(label='Current Year', renderers=[bokeh_figure.renderers[0]])
        li2 = LegendItem(label='Prior Year', renderers=[bokeh_figure.renderers[1]])

        # only add target if applicable for the pollutant
        if len(targets_df) > 0:
            glyph_target = Line(x="date", y="target", line_color="#B5B5B6", line_width=3, line_alpha=1)
            bokeh_figure.add_glyph(source, glyph_target)
            li3 = LegendItem(label='Target Level', renderers=[bokeh_figure.renderers[2]])
            legend1 = Legend(items=[li1, li2, li3], location='top_center')
        else:
            legend1 = Legend(items=[li1, li2], location='top_center')

        bokeh_figure.add_layout(legend1)

    if not daily_api_sucess:
        data = {'date': [start_date,end_date],
                'y': [0,1],
                'name_display' : ['No data avaliable for ' + pollutant + '\nduring selected date range','']
        }
        
        #Remove y grid to keep things clean
        bokeh_figure.ygrid.grid_line_color = None
        
        # Create DataFrame 
        blank_df = pd.DataFrame(data) 
        blank_df['date'] = pd.to_datetime(blank_df['date'])
        source = ColumnDataSource(blank_df)
        
        glyph = Text(x='date', y='y', text='name_display', text_color="#B5B5B6")
        
        #Add glyph to the Bokeh canvas
        bokeh_figure.add_glyph(source, glyph)
        
    # script, div = components(bokeh_figure)
    item = json_item(bokeh_figure)
    
    # return render(request, 'airpollution/time-series.html', dict(script=script, div=div))
    return JsonResponse(item)
