from django.contrib import admin

# Register your models here.
from airpollution.models import ObservationStationReading, ObservationStation, Measurement, Pollutant, Target
from airpollution.models.models import EUStat, ChartViz
from airpollution.models.models_copernicus import SatelliteImageFiles
from airpollution.models.models_nuts import NutsRegions, EUCountries
from airpollution.models.models_eea import EEADataModel
from airpollution.models.models_eurostat_population import EurostatDataModel

admin.site.register(EUStat)
admin.site.register(ChartViz)


class EurostatDataModelAdmin(admin.ModelAdmin):
    list_display = ('year', 'population', 'nutsRegionStr', 'nutsRegion')
    list_filter = ('year', 'nutsRegionStr', 'nutsRegion')


admin.site.register(EurostatDataModel, EurostatDataModelAdmin)


class EUCountriesAdmin(admin.ModelAdmin):
    list_display = ('key', 'nuts_region')


admin.site.register(EUCountries, EUCountriesAdmin)


class EEADataModelAdmin(admin.ModelAdmin):
    list_display = ('year', 'pollutant_name', 'country', 'sector', 'sector_group', 'emissions')
    list_filter = ('pollutant_name', 'country', 'sector', 'sector_group')  # will allow items to be filtered


admin.site.register(EEADataModel, EEADataModelAdmin)


class SatelliteImageFilesAdmin(admin.ModelAdmin):
    list_display = ('date', 'pollutant', 'category', 'shape', 'file_path')
    list_filter = ('date', 'pollutant')  # will allow items to be filtered


admin.site.register(SatelliteImageFiles, SatelliteImageFilesAdmin)


class ObservationStationReadingAdmin(admin.ModelAdmin):
    list_display = ('date_time', 'country_code', 'air_quality_station', 'pollutant', 'value', 'validity', 'verification')
    list_filter = ('date_time', 'country_code', 'pollutant', 'validity', 'verification')  # will allow items to be filtered


admin.site.register(ObservationStationReading, ObservationStationReadingAdmin)


class ObservationStationAdmin(admin.ModelAdmin):
    list_display = ('air_quality_station', 'country_code', 'nuts_1', 'nuts_2', 'nuts_3', 'air_quality_station_area')
    list_filter = ('country_code', 'air_quality_station_area')  # will allow items to be filtered


admin.site.register(ObservationStation, ObservationStationAdmin)


class NutsRegionsAdmin(admin.ModelAdmin):
    list_display = ('key', 'EU_MEMBER', 'LEVL_CODE', 'NUTS_ID', 'CNTR_CODE', 'NUTS_NAME', 'FID')
    list_filter = ('LEVL_CODE', 'CNTR_CODE', 'EU_MEMBER')  # will allow items to be filtered


admin.site.register(NutsRegions, NutsRegionsAdmin)


class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('measurement', 'description')  # field will be displayed in column


admin.site.register(Measurement, MeasurementAdmin)


class PollutantAdmin(admin.ModelAdmin):
    list_display = ('key', 'copernicus_key', 'observation_key', 'eea_key')  # field will be displayed in column
    list_filter = ('copernicus_key', 'observation_key', 'eea_key')


admin.site.register(Pollutant, PollutantAdmin)


class TargetAdmin(admin.ModelAdmin):
    list_display = ('id', 'measurement', 'pollutant', 'unit', 'value', 'count_limit')
    list_filter = ('measurement', 'pollutant')  # will allow items to be filtered


admin.site.register(Target, TargetAdmin)



