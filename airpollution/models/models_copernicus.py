"""
Author: Mark McDonald
This script includes models that support data
originating from the Copernicus dataset.
"""
import netCDF4
import numpy as np
from django.core.validators import validate_comma_separated_integer_list
from django.db import models

from airpollution.models.models_pollutants import Pollutant


class SatelliteImageFiles(models.Model):
    """
    Each record holds parameters of data that are contained in a file.
    The file path is saved in this record.
    The shape of the images are in a 4 dimensions. (hours, levels, height, width)
    """
    key = models.CharField(max_length=128, primary_key=True)
    date = models.CharField(max_length=10, db_index=True)
    date_time = models.DateTimeField(null=True, db_index=True)
    pollutant = models.ForeignKey(Pollutant, on_delete=models.CASCADE, related_name="satellite_images", db_index=True)
    description = models.CharField(max_length=64)
    model = models.CharField(max_length=64)
    category = models.CharField(max_length=10)
    bbox_minlon = models.FloatField()
    bbox_maxlon = models.FloatField()
    bbox_minlat = models.FloatField()
    bbox_maxlat = models.FloatField()
    levels = models.CharField(validators=[validate_comma_separated_integer_list], max_length=64)
    hours = models.CharField(validators=[validate_comma_separated_integer_list], max_length=128, db_index=True)
    year = models.IntegerField(db_index=True)
    month = models.IntegerField(db_index=True)
    day = models.IntegerField(db_index=True)
    shape = models.CharField(validators=[validate_comma_separated_integer_list], max_length=32)
    file_path = models.FileField(upload_to='satellite_files', max_length=512)
    image = models.CharField(max_length=3600000, blank=True)

    @staticmethod
    def get_sat_image(pollutant: str, year: int, month: int, day: int,
                      category: str = 'ANALYSIS',
                      hour: int = 12,
                      level: int = 0):
        """
        A numpy array of the image.
        :param pollutant: The pollutant key code
        :param year: Year of image
        :param month: Month of image
        :param day: Day of image
        :param category: ANALYSIS or FORECAST
        :param hour: Hour of image
        :param level: Altitude of image
        :return: Rendered HTML page with image
        """
        # determine the nc file to retrieve

        # get the pollutant object and the copernicus lookup key
        pollutant_obj = Pollutant.objects.get(pk=pollutant)
        # cop_key = str(pollutant_obj.copernicus_key)

        rs = SatelliteImageFiles.objects.get(pollutant=pollutant_obj,
                                             year=year, month=month, day=day,
                                             category=category)

        new_shape = [int(x) for x in rs.shape.split(" ")]
        img = np.array([float(x) for x in rs.image.split(" ")]).reshape(new_shape)

        return img

        # filepath = str(rs.file_path)
        #
        # # extract the images
        # ds = netCDF4.Dataset(filepath)
        #
        # return ds[cop_key][hour, level, :]

    # @staticmethod
    # def get_dayavg_sat_image(pollutant: str, year: int, month: int, day: int,
    #                          category: str = 'ANALYSIS', level: int = 0):
    #     """
    #     A numpy array of the average of images over a day.
    #     :param pollutant: The pollutant key code
    #     :param year: Year of image
    #     :param month: Month of image
    #     :param day: Day of image
    #     :param category: ANALYSIS or FORECAST
    #     :param level: Altitude of image
    #     :return: Rendered HTML page with image
    #     """
    #     # get composite average for the day
    #     rs = SatelliteImageFiles.objects.get(pollutant=pollutant,
    #                                          year=year,
    #                                          month=month,
    #                                          day=day,
    #                                          category=category)
    #
    #     new_shape = [int(x) for x in rs.shape.split(" ")]
    #     img = np.array([float(x) for x in rs.image.split(" ")]).reshape(new_shape)
    #
    #     return img
    #
    #     # filepath = str(day_file_rs.file_path)
    #     # ds = netCDF4.Dataset(filepath)
    #     #
    #     # cop_key = Pollutant.objects.get(pk=pollutant).copernicus_key
    #     #
    #     # images = ds[cop_key][:, level, :]
    #
    #     # return images.mean(axis=0)

    @staticmethod
    def get_dayavg_sat_images(pollutants: list, year: int, month: int, day: int,
                              category: str = 'ANALYSIS', level: int = 0) -> dict:
        """
        A numpy array of the average of images over a day.
        :param pollutants: A list pollutant key codes
        :param year: Year of image
        :param month: Month of image
        :param day: Day of image
        :param category: ANALYSIS or FORECAST
        :param level: Altitude of image
        :return: Rendered HTML page with image
        """
        # get composite average for the day
        day_file_rs = SatelliteImageFiles.objects.filter(pollutant__in=pollutants,
                                                         # year=year,
                                                         # month=month,
                                                         # day=day,
                                                         category=category)

        images = {}
        for rs in day_file_rs:
            new_shape = [int(x) for x in rs.shape.split(" ")]
            img = np.array([float(x) for x in rs.image.split(" ")]).reshape(new_shape)
            images.update({rs.pollutant.key: img})

            # ds = netCDF4.Dataset(str(rs.file_path))
            # cop_key = Pollutant.objects.get(pk=rs.pollutant).copernicus_key
            # images.update({rs.pollutant.key: ds[cop_key][:, level, :].mean(axis=0)})

        return images

    @staticmethod
    def get_most_recent_date():
        dates = [d.get('date_time') for d in SatelliteImageFiles.objects.all().values('date_time')]
        return np.max(dates)


# class PollutionByLocation(models.Model):
#     """
#     This is for pollution data where our objective is:
#     import numpy
#     vals = query the data
#     vals.sort()
#     val = numpy.mean(vals) | numpy.median(vals) | numpy.mode(vals)
#
#     @todo how to reference EUCountryCode? this is in models.py
#     country = models.ForeignKey(EUCountryCode, on_delete=models.CASCADE, blank=False, null=True)
#     """
#     the_date = models.DateField()
#     pollutant_name = models.CharField(max_length=20, db_index=True)
#     unit = models.CharField(max_length=20)
#     recorded_value = models.DecimalField(decimal_places=2, max_digits=6)
#     station_identifier = models.CharField(max_length=50)
