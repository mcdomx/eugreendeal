import json
import math

import pandas as pd
from bokeh.embed import json_item
from bokeh.models import ColumnDataSource, HTMLTemplateFormatter, TableColumn, DataTable
from django.http import JsonResponse

from airpollution.models import Target, Pollutant, EU_ISOCODES, ObservationStationReading
from airpollution.views.aq_api_v1 import annual


def draw_plot(request, years: list = None, countries: list = None, pollutants: list = None, verbosity: int = 0):
    """
    Returns a rendered map with a script and div object.
    :param request: Django request
    :param years: The years to of data
    :param countries: The country code of the regions to be plotted (eg: de, nl, fr)
    :param pollutants: The pollutant to be plotted (eg: o3, co)
    :param verbosity: Specifies what level of errors or warnings to be logged (default: 0)
    :return: Returns Bokeh JSON object
    """
    if request is not None:
        countries = request.GET.get('countries', None)
        years = request.GET.get('years', None)
        pollutants = request.GET.get('pollutants', None)
        verbosity = request.GET.get('verbosity', 0)

    # get Target pollutants
    t_pollutants = [x.get('pollutant_id') for x in
                    Target.objects.filter(measurement='calendar_year').values('pollutant_id')]

    # get the Observation station readings pollutant names for selected target-relevant pollutants
    if pollutants is None:
        pollutants = t_pollutants
    else:
        pollutants_lookup = {k: v.key for k, v in Pollutant.get_observation_pollutants().items() if v.key in pollutants}
        pollutants = list(pollutants_lookup.values())

    if countries is None:
        countries = EU_ISOCODES

    if years is None:
        years = []
        u_years_rs = ObservationStationReading.objects.filter(country_code__in=countries, validity=1,
                                                              pollutant__in=map(str.upper, pollutants)).values(
            'date_time__year').distinct()
        for item in u_years_rs:
            years.append(list(item.values())[0])
    years.sort()

    # get data for countries for selected pollutants
    annual_dict = annual(request, years=years, countries=countries, pollutants=pollutants, verbosity=verbosity)
    annual_dict = json.loads(annual_dict.content.decode())

    # create a dataframe of actual pollutant averages per year, country and pollutant
    annual_df = pd.DataFrame()
    for c, years_dict in annual_dict.items():
        xdf = pd.DataFrame(years_dict).reset_index().rename(columns={'index': 'pollutant'})
        xdf.insert(0, 'country', c)
        annual_df = annual_df.append(xdf)
    annual_df = annual_df.reset_index(drop=True)

    # get targets
    t_df = Pollutant.get_targets_df(years=[years[-1]], pollutants=pollutants)
    t_df = t_df[t_df.measurement_id == 'calendar_year']
    t_df = t_df[['country', 'pollutant_id', 'value']].rename \
        (columns={'pollutant_id': 'pollutant', 'value': 'target_value'})

    # merge targets with actuals
    annual_df = annual_df.merge(t_df)

    # add vs. Target Columns
    def per_fmt(s):
        if math.isnan(s):
            return '-'
        return f"{s:0.1%}"

    # for each year, add a comparison vs target column
    for y in years:
        idx = list(annual_df.columns).index(str(y))
        new_col = annual_df[str(y)] / annual_df['target_value']
        new_col = new_col.apply(per_fmt)
        annual_df.insert(idx + 1, f"{y} vs. Target", new_col)

    # format nan values
    def fmt(s):
        rv = round(s, 2)
        if math.isnan(rv):
            rv = '-'
        return rv

    for y in years:
        annual_df[str(y)] = annual_df[str(y)].apply(fmt)

    vsTarget_template = """
                <div style="text-align:right; color:<%= (function colorfromfloat(){
                                                                    if(parseFloat(value.substring(0, value.length-1))<100){
                                                                        return("green")}
                                                                    else{return("red")}
                                                                    }()) %>; 
                                    "> 
                <%= value %></div>
                """

    vsTarget_formater = HTMLTemplateFormatter(template=vsTarget_template)

    source = ColumnDataSource(annual_df)

    val_template = """<div style="text-align:right;"><%= value %></div>"""
    val_formatter = HTMLTemplateFormatter(template=val_template)

    columns = [
        TableColumn(field="country", title="Country"),
        TableColumn(field="pollutant", title="Pollutant"),
        TableColumn(field='target_value', title="Target", formatter=val_formatter)
    ]

    for y in years:
        columns.append(TableColumn(field=str(y), title=str(y), formatter=val_formatter))
        columns.append(TableColumn(field=f"{y} vs. Target", title=f"{y} vs. Target", formatter=vsTarget_formater))

    data_table = DataTable(source=source, columns=columns, width=800, height=400, index_position=None,
                           sizing_mode='stretch_both')

    # jupyter notebook
    # return data_table

    # django
    data_table = json_item(data_table)

    return JsonResponse(data_table)
