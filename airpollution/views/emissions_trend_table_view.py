from bokeh.embed import json_item
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter

from airpollution.models import *


def draw_plot(request) -> JsonResponse:
    """
    Draws a table with emissions by year by country for most recent 5 years available.
    :param request: A Django request that conttans the pollutants to be filtered
    :return: JsonResponse that contains a Bokeh plot to be rendered in an HTML view
    """
    # get end of year pollution values for pollutants with targets

    # get Target pollutants
    pollutants = [x.get('pollutant_id') for x in Target.objects.filter(measurement='calendar_year').values('pollutant_id')]

    # get the EEA pollutant names for selected pollutants
    eea_lookup = {k: v.key for k, v in Pollutant.get_eea_pollutants().items() if v.key in pollutants}
    eea_pollutants = list(eea_lookup.keys())

    # get data for countries for selected pollutats
    rs = EEADataModel.objects.filter(country__in=EU_ISOCODES, sector='NATIONAL_TOTAL', sector_group='NATIONAL_TOTAL', pollutant_name__in=eea_pollutants).values()

    rs_df = pd.DataFrame(rs)

    # drop unneeded columns
    rs_df = rs_df[['year', 'pollutant_name', 'country', 'emissions']]

    # rename pollutant to application key values
    rs_df['pollutant_name'] = rs_df.apply(lambda s: eea_lookup.get(s.pollutant_name), axis=1)

    # rename columns
    rs_df.rename(columns={'pollutant_name':'pollutant', 'emissions':'value'}, inplace=True)

    # turn years into strings
    rs_df['year'] = rs_df.apply(lambda s: str(s.year), axis=1)

    # format
    rs_df['value'] = rs_df['value'].astype(float)

    # create formatted pivot table for bokeh
    rs_df_pivot = rs_df.pivot_table(index=['country', 'pollutant'], columns=['year'], values='value')
    rs_df_pivot = rs_df_pivot.reset_index()
    rs_df_pivot.index.name = 'index'
    rs_df_pivot.sort_values(by=['country', 'pollutant'], inplace=True)

    # display data as a table
    years = rs_df_pivot.columns
    years = years[-5:]  # pick the most recent 5 years available
    source = ColumnDataSource(rs_df_pivot)

    val_template = """<div style="text-align:right;"><%= value %></div>"""
    val_formatter = HTMLTemplateFormatter(template=val_template)

    columns = [
                TableColumn(field="country", title="Country"),
                TableColumn(field="pollutant", title="Pollutant"),
              ]

    for y in years:
        columns. append(TableColumn(field=y, title=y, formatter=val_formatter))

    data_table = DataTable(source=source, columns=columns, height=280, index_position=None, sizing_mode='stretch_both')

    # jupyter notebook
    # return data_table

    # django
    data_table = json_item(data_table)

    return JsonResponse(data_table)

