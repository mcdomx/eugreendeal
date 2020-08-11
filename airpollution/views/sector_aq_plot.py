"""
Author: Hemant Bajpai
Creates bokeh div element for EEA data source.

"""
from bokeh.embed import json_item
from bokeh.models import ColumnDataSource, HoverTool, Text
from bokeh.models import Legend
from bokeh.palettes import Spectral9, Spectral6
from bokeh.plotting import figure
from django.http import JsonResponse
from airpollution.models import EEADataModel

def draw_plot(request):
    """
    Returns a rendered map with a script and div object.
    :param request: Django request which contains the countries filtered
    :return: Returns a JSON Bokeh object to be rendered in an html view
    """

    # Getting the country and year from input
    country = request.GET.get('countries', None)

    year = 2017
    pollutants = ['PM2.5', 'PM10', 'NOx', 'CO', 'SOx', 'NH3']
    sectors = ['Agriculture', 'Commercial, institutional and households', 'Energy production and distribution',
               'Energy use in industry', 'Industrial processes and product use', 'Non-road transport', 'Road transport',
               'Waste', 'Other']
    colors = Spectral9

    # Geting the data as needed by bokeh plot
    data = {}
    data['pollutants'] = pollutants

    total_pm25 = 0
    total_pm10 = 0
    total_nox = 0
    total_co = 0
    total_sox = 0
    total_nh3 = 0

    # Creating figure
    p = figure(x_range=pollutants, plot_height=500, plot_width=1200, sizing_mode='stretch_width',
               toolbar_location=None, tools="hover", tooltips="$name @pollutants: @$name")

    try:
        response_pm25 = EEADataModel.get_sectors_info(year=year, country_code=country, pollutant='PM2.5')
        response_pm10 = EEADataModel.get_sectors_info(year=year, country_code=country, pollutant='PM10')
        response_nox = EEADataModel.get_sectors_info(year=year, country_code=country, pollutant='NOx')
        response_co = EEADataModel.get_sectors_info(year=year, country_code=country, pollutant='CO')
        response_sox = EEADataModel.get_sectors_info(year=year, country_code=country, pollutant='SOx')
        response_nh3 = EEADataModel.get_sectors_info(year=year, country_code=country, pollutant='NH3')
        sector_api_sucess = True

        if not response_pm25:
            sector_api_sucess = False
    except:
        sector_api_sucess = False

    if sector_api_sucess:
        for sector in sectors:
            list = []

            if sector is 'Other':
                list.append(100 - total_pm25)
            else:
                total = response_pm25[country][year]['PM2.5']['NATIONAL_TOTAL']
                emission = 0
                if sector in response_pm25[country][year]['PM2.5']:
                    emission = response_pm25[country][year]['PM2.5'][sector] * 100 / total
                total_pm25 += emission
                list.append(emission)

            if sector is 'Other':
                list.append(100 - total_pm10)
            else:
                total = response_pm10[country][year]['PM10']['NATIONAL_TOTAL']
                emission = 0
                if sector in response_pm10[country][year]['PM10']:
                    emission = response_pm10[country][year]['PM10'][sector] * 100 / total
                total_pm10 += emission
                list.append(emission)

            if sector is 'Other':
                list.append(100 - total_nox)
            else:
                total = response_nox[country][year]['NOx']['NATIONAL_TOTAL']
                emission = 0
                if sector in response_nox[country][year]['NOx']:
                    emission = response_nox[country][year]['NOx'][sector] * 100 / total
                total_nox += emission
                list.append(emission)

            if sector is 'Other':
                list.append(100 - total_co)
            else:
                emission = 0
                total = response_co[country][year]['CO']['NATIONAL_TOTAL']
                if sector in response_co[country][year]['CO']:
                    emission = response_co[country][year]['CO'][sector] * 100 / total
                total_co += emission
                list.append(emission)

            if sector is 'Other':
                list.append(100 - total_sox)
            else:
                emission = 0
                total = response_sox[country][year]['SOx']['NATIONAL_TOTAL']
                if sector in response_sox[country][year]['SOx']:
                    emission = response_sox[country][year]['SOx'][sector] * 100 / total
                total_sox += emission
                list.append(emission)

            if sector is 'Other':
                list.append(100 - total_nh3)
            else:
                total = response_nh3[country][year]['NH3']['NATIONAL_TOTAL']
                emission = 0
                if sector in response_nh3[country][year]['NH3']:
                    emission = response_nh3[country][year]['NH3'][sector] * 100 / total
                total_nh3 += emission
                list.append(emission)

            data[sector] = list

        v = p.vbar_stack(sectors, x='pollutants', width=0.5, color=colors, source=data)

        # Adding legends
        legend = Legend(items=[(x, [v[i]]) for i, x in enumerate(sectors)], location=(10, 100))

        p.add_layout(legend, 'right')

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

    # Error handling
    if not sector_api_sucess:
        x = [0]
        y = [0]
        name_display = ['No data avaliable for selected country']

        # Remove y grid to keep things clean
        p.ygrid.grid_line_color = None
        source = ColumnDataSource(dict(x=x, y=y, name_display=name_display))
        glyph = Text(x='x', y='y', text='name_display', text_color="#B5B5B6")
        p.add_glyph(source, glyph)

    item = json_item(p)
    return JsonResponse(item)


def draw_yearly_emission_plot(request):
    """
    Returns a rendered yearly emissions plot with a script and div object.
    :param request: Django request
    :param country: The country code of the regions to be mapped (eg: de, nl, fr)
    :return: Returns a rendered map with a script and div object.
    """

    # Getting the country and year from input
    country = request.GET.get('countries', None)

    pollutants = ['PM2.5', 'PM10', 'NOx', 'CO', 'SOx', 'NH3']

    list_pm25 = []
    list_pm10 = []
    list_nox = []
    list_co = []
    list_sox = []
    list_nh3 = []

    years = []

    # Getting data from model
    try:
        response_pm25 = EEADataModel.get_sectors_info(year="", country_code=country, pollutant='PM2.5',
                                                      sector_group='NATIONAL_TOTAL')
        response_pm10 = EEADataModel.get_sectors_info(year="", country_code=country, pollutant='PM10',
                                                      sector_group='NATIONAL_TOTAL')
        response_nox = EEADataModel.get_sectors_info(year="", country_code=country, pollutant='NOx',
                                                     sector_group='NATIONAL_TOTAL')
        response_co = EEADataModel.get_sectors_info(year="", country_code=country, pollutant='CO',
                                                    sector_group='NATIONAL_TOTAL')
        response_sox = EEADataModel.get_sectors_info(year="", country_code=country, pollutant='SOx',
                                                     sector_group='NATIONAL_TOTAL')
        response_nh3 = EEADataModel.get_sectors_info(year="", country_code=country, pollutant='NH3',
                                                     sector_group='NATIONAL_TOTAL')
        sector_api_sucess = True

        if not response_pm25:
            sector_api_sucess = False
    except:
        sector_api_sucess = False

    # Creating figure
    p = figure(plot_width=1200, plot_height=500, sizing_mode='stretch_width', toolbar_location=None,
               border_fill_color=None, min_border_left=0, )

    p.xgrid.grid_line_color = None
    p.xaxis.axis_line_color = None
    p.yaxis.axis_line_color = None
    p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

    if sector_api_sucess:
        for year in range(1990, 2017):
            years.append(year)
            list_pm25.append(response_pm25[country][year]['PM2.5']['NATIONAL_TOTAL'])
            list_pm10.append(response_pm10[country][year]['PM10']['NATIONAL_TOTAL'])
            list_nox.append(response_nox[country][year]['NOx']['NATIONAL_TOTAL'])
            list_co.append(response_co[country][year]['CO']['NATIONAL_TOTAL'])
            list_sox.append(response_sox[country][year]['SOx']['NATIONAL_TOTAL'])
            list_nh3.append(response_nh3[country][year]['NH3']['NATIONAL_TOTAL'])

        colors = Spectral6
        source = ColumnDataSource(data=dict(
            xs=[years, years, years, years, years, years],
            ys=[list_pm25, list_pm10, list_nox, list_co, list_sox, list_nh3],
            colors=colors,
            legends=pollutants
        ))

        p.multi_line(xs='xs', ys='ys', source=source, color='colors', legend='legends', line_width=3)
        p.yaxis.axis_label = 'Gg (1000 tonnes)'
        p.add_tools(HoverTool(tooltips=[
            ('Year', '$data_x'),
            ('Emission', '$data_y')]
        ))

    # Error handling
    if not sector_api_sucess:
        x = [0]
        y = [0]
        name_display = ['No data avaliable for selected country']

        # Remove y grid to keep things clean
        p.ygrid.grid_line_color = None
        source = ColumnDataSource(dict(x=x, y=y, name_display=name_display))
        glyph = Text(x='x', y='y', text='name_display', text_color="#B5B5B6")
        p.add_glyph(source, glyph)

    item = json_item(p)
    return JsonResponse(item)


def draw_emission_distribution_plot(request):
    """
    Returns a rendered yearly emission distribution plot with a script and div object.
    :param request: Django request
    :param pollutant: The pollutant name
    :return: Returns a rendered map with a script and div object.
    """
    country = request.GET.get("countries", None)
    pollutant = request.GET.get('pollutant', None)

    list_agriculture = []
    list_commercial = []
    list_energyP = []
    list_energyU = []
    list_industrial = []
    list_nonroadT = []
    list_roadT = []
    list_waste = []
    list_other = []

    sectors = ['Agriculture', 'Commercial, institutional and households', 'Energy production and distribution',
               'Energy use in industry', 'Industrial processes and product use', 'Non-road transport', 'Road transport',
               'Waste', 'Other']

    years = []

    try:
        response = EEADataModel.get_sectors_info(year="", country_code=country, pollutant=pollutant)
        sector_api_sucess = True

        if not response:
            sector_api_sucess = False
    except:
        sector_api_sucess = False

    # Creating figure
    p = figure(plot_width=600, plot_height=500, toolbar_location=None, border_fill_color=None,
               sizing_mode='stretch_width', min_border_left=0)
    p.xgrid.grid_line_color = None
    p.xaxis.axis_line_color = None
    p.yaxis.axis_line_color = None
    p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

    if sector_api_sucess:
        for year in range(1990, 2017):
            years.append(year)
            agriculture = 0
            if 'Agriculture' in response[country][year][pollutant]:
                agriculture = response[country][year][pollutant]['Agriculture']
            list_agriculture.append(agriculture)
            commercial = 0
            if 'Commercial, institutional and households' in response[country][year][pollutant]:
                commercial = response[country][year][pollutant]['Commercial, institutional and households']
            list_commercial.append(commercial)
            energyP = 0
            if 'Energy production and distribution' in response[country][year][pollutant]:
                energyP = response[country][year][pollutant]['Energy production and distribution']
            list_energyP.append(energyP)
            energyU = 0
            if 'Energy use in industry' in response[country][year][pollutant]:
                energyU = response[country][year][pollutant]['Energy use in industry']
            list_energyU.append(energyU)
            industrial = 0
            if 'Industrial processes and product use' in response[country][year][pollutant]:
                industrial = response[country][year][pollutant]['Industrial processes and product use']
            list_industrial.append(industrial)
            nonroadT = 0
            if 'Non-road transport' in response[country][year][pollutant]:
                nonroadT = response[country][year][pollutant]['Non-road transport']
            list_nonroadT.append(nonroadT)
            roadT = 0
            if 'Road transport' in response[country][year][pollutant]:
                roadT = response[country][year][pollutant]['Road transport']
            list_roadT.append(roadT)
            waste = 0
            if 'Waste' in response[country][year][pollutant]:
                waste = response[country][year][pollutant]['Waste']
            list_waste.append(waste)
            other = 0
            if 'NATIONAL_TOTAL' in response[country][year][pollutant]:
                other = response[country][year][pollutant][
                            'NATIONAL_TOTAL'] - agriculture - commercial - energyP - energyU - industrial - nonroadT - roadT - waste
            list_other.append(other)

        colors = Spectral9
        source = ColumnDataSource(data=dict(
            xs=[years, years, years, years, years, years, years, years, years],
            ys=[list_agriculture, list_commercial, list_energyP, list_energyU,
                list_industrial, list_nonroadT, list_roadT, list_waste, list_other],
            labels=sectors,
            colors=colors
        ))

        r = p.multi_line(xs='xs', ys='ys', source=source, color='colors', line_width=3)

        p.add_tools(HoverTool(tooltips=[
            ('Sector', '@labels'),
            ('Year', '$data_x'),
            ('Emission', '$data_y')]
        ))

        p.yaxis.axis_label = 'Gg (1000 tonnes)'

    # Error handling
    if not sector_api_sucess:
        x = [0]
        y = [0]
        name_display = ['No data avaliable for ' + pollutant + '\nfor selected country']

        # Remove y grid to keep things clean
        p.ygrid.grid_line_color = None
        source = ColumnDataSource(dict(x=x, y=y, name_display=name_display))
        glyph = Text(x='x', y='y', text='name_display', text_color="#B5B5B6")
        p.add_glyph(source, glyph)

    item = json_item(p)
    return JsonResponse(item)
