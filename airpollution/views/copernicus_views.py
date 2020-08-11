"""
Author: Mark McDonald
Views specific to the copernicus data
"""

import base64
import io

import numpy as np
from PIL import Image
from django.shortcuts import render

from airpollution.models import SatelliteImageFiles


def get_sat_image(request, pollutant: str, year: int, month: int, day: int, category: str = 'ANALYSIS', hour: int = 12,
                  level: int = 0):
    """
    Render a satellite image HTML page.
    :param request: Django request
    :param pollutant: The pollutant key code
    :param year: Year of image
    :param month: Month of image
    :param day: Day of image
    :param category: ANALYSIS or FORECAST
    :param hour: Hour of image
    :param level: Altitude of image
    :return: Rendered HTML page with image
    """
    image = SatelliteImageFiles.get_sat_image(pollutant=pollutant, year=year, month=month, day=day,
                                              category=category,
                                              hour=hour, level=level)

    # convert to base64 for HTML display
    img_base64 = _convert_imgarray_to_inmem_base64_png(image)

    return render(request, 'airpollution/test-satimages.html', dict(img_base64=img_base64))



def _convert_imgarray_to_inmem_base64_png(img_array: np.array) -> base64:
    """
    ref: https://stackoverflow.com/questions/42503995/how-to-get-a-pil-image-as-a-base64-encoded-string
    Convert an image array into an in-memory base64 PNG image.
    The return value can be placed in an HTML src tag:
    <img src="data:image/png;base64,<<base64 encoding>>" height="" width="" alt="image">
    :param img_array: a numpy image
    :return: base64 image in ascii characters
    """

    pngimg = Image.new(mode='P', size=img_array.T.shape)  # create new in-memory image
    # pngimg.putpalette([
    #     255, 255, 255,  # white background
    #     50, 100, 50,  # index 1 is green
    #     255, 255, 0,  # index 2 is yellow
    #     200, 0, 0,  # index 3 is red
    # ])
    pngimg.putdata([pixel for pixel in np.ravel(img_array)])  # scale=10 <- will multiple each pixel value

    b = io.BytesIO()  # create an empty byte object
    pngimg.save(b, format="PNG")  # save the png file to the object
    b.seek(0)  # move pointer back to the start of memory space
    img_bytes = b.read()  # read memory space

    base64_img = base64.b64encode(img_bytes)  # encode the image to base64
    base64_ascii_img = base64_img.decode('ascii')  # finally, decode it to ascii characters

    return base64_ascii_img
