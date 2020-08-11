from django.urls import path
from django.urls import re_path

from .views import views
from .views import copernicus_views
from .views import aq_api_v1
from .views import eea_station_views
from .views import nuts_maps_views
from .views import daily_aq_map
from .views import pollution_over_time_view
from .views import pollution_deltas_table_view
from .views import pollution_regional_deltas_table_view
from .views import pollution_attainment_by_year_table_view
from .views import emissions_trend_table_view
from .views import target_heatmap_view
from .views import sector_aq_plot

urlpatterns = [
    
    #Air Quality routes
    path("aq_api/daily", aq_api_v1.daily, name="daily"),
    path("aq_api/annual", aq_api_v1.annual, name="annual"),
    path("aq_api/sectors", aq_api_v1.sectors, name="sectors"),
    path("aq_api/targets", aq_api_v1.targets, name="targets"),

    #Region Routes
    path("aq_api/region_info", aq_api_v1.region_info, name="region_info"),
    path("aq_api/region_boundaries", aq_api_v1.region_boundaries, name="region_boundaries"),


    # Default route
    path("", views.index_view, name="index"),

    path("dashboard", views.dashboard_view, name="dashboard"),
    
    path("trends", views.trends_view, name="trends"),

    path("regional", views.regional_view, name="regional"),

    path("sectors", views.sectors_view, name="sectors"),
    
    path("pollution-over-time", views.pollution_over_time_view, name="pollution-over-time"),
    
    path("pollution-deltas-table", views.pollution_deltas_table_view, name="pollution-deltas-table"),
    
    path("pollution-deltas-regional-table", views.pollution_deltas_regional_table_view, name="pollution-deltas-regional-table"),

    path("map-target-bubbles", views.target_bubblemap_view, name="bubblemap"),

    path("map-target-heatmap", views.target_heatmap_view, name="heatmap"),

    path("pollution-attainment-table", views.pollution_attainment_table_view, name="pollution-attainment-table"),

    path("emissions-trend-table", views.emissions_trend_table_view, name="emissions-trend-table"),

    path("goal", views.goals_view, name="goal"),

    path("login", views.login_view, name="login"),

    path("logout", views.logout_view, name="logout"),

    path("admin", views.admin_view, name="admin"),

    path("admin_persona", views.admin_persona_view, name="admin_persona"),

    path("user_persona", views.user_persona_view, name="user_persona"),

    path("change_user_persona/<int:user_id>/<int:group_id>/<str:context_url>", views.change_user_persona,
         name="change_user_persona"),

    path("delete_user/<int:user_id>/<str:context_url>", views.delete_user,
         name="delete_user"),

    path("add_user", views.add_user, name="add_user"),

    path("add_chart_to_persona/", views.add_chart_to_persona,
         name="add_chart_to_persona"),

    path("delete_chart_from_persona/<int:group_id>/<str:chart_id>", views.delete_chart_from_persona,
         name="delete_chart_from_persona"),

    path("add_persona", views.add_persona, name="add_persona"),

    path("delete_persona/<int:persona_id>/<str:context_url>", views.delete_persona, name="delete_persona"),

    path("view_group/<int:group_id>", views.view_group, name="view_group"),

    path("satimage/<str:pollutant>/<int:year>/<int:month>/<int:day>", copernicus_views.get_sat_image, name="satimages"),

    re_path(r"nutsmap[\/|\?].*", nuts_maps_views.get_nuts_map_data, name="nutsmaps"),



    path("nutsmapdata", nuts_maps_views.get_nuts_map_data, name="nutsmapdata"),

    #path("daily_aq/nuts_level=<int:nuts_level>&countries=<str:country>&pollutant=<str:pollutant>&start_date=<str:start_date>&end_date=<str:end_date>", daily_aq_map.draw_map, name="daily_aq"),
    re_path(r"daily_aq[\/|\?].*", daily_aq_map.draw_map, name="daily_aq"),

    re_path(r"sectors_aq_1[\/|\?].*", sector_aq_plot.draw_plot, name="sectors_aq_1"),

    re_path(r"sectors_aq_2[\/|\?].*", sector_aq_plot.draw_yearly_emission_plot, name="sectors_aq_2"),

    #path("pollution_over_time/nuts_level=<int:nuts_level>&countries=<str:country>&pollutant=<str:pollutant>&start_date=<str:start_date>&end_date=<str:end_date>", daily_aq_map.draw_map, name="daily_aq"),
    re_path(r"pollution_over_time[\/|\?].*", pollution_over_time_view.draw_plot, name="pollution_over_time"),

    re_path(r"emission_over_time[\/|\?].*", sector_aq_plot.draw_emission_distribution_plot, name="emission_over_time"),
    
    #path("pollution_deltas_table/nuts_level=<int:nuts_level>&countries=<str:country>&pollutant=<str:pollutant>&start_date=<str:start_date>&end_date=<str:end_date>", daily_aq_map.draw_map, name="daily_aq"),
    re_path(r"pollution_deltas_table[\/|\?].*", pollution_deltas_table_view.draw_plot, name="pollution_deltas_table"),

    #path("pollution_regional_deltas_table/nuts_level=<int:nuts_level>&countries=<str:country>&pollutant=<str:pollutant>&start_date=<str:start_date>&end_date=<str:end_date>", daily_aq_map.draw_map, name="daily_aq"),
    re_path(r"pollution_regional_deltas_table[\/|\?].*", pollution_regional_deltas_table_view.draw_plot, name="pollution_regional_deltas_table"),

    re_path(r"map_target_bubbles[\/|\?].*", nuts_maps_views.draw_bubble_map),

    re_path(r"map_target_heatmap[\/|\?].*", target_heatmap_view.draw_heatmap),

    re_path(r"pollution_attainment_table[\/|\?].*", pollution_attainment_by_year_table_view.draw_plot),

    re_path(r"emissions_trend_table[\/|\?].*", emissions_trend_table_view.draw_plot),

    path("aq_api/v1/<int:example_val>", aq_api_v1.region_info, name="nuts regions"),

    path("get_stations", eea_station_views.get_stations, name="get all stations"),
    path("get_stations/<str:station_name>", eea_station_views.get_stations, name="get station by name"),

]
