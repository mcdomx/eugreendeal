# Satellite Images
Satellite images of pollution in the air is collected from the Copernicus website.  The functions and classes described below explain how to extract data from the Copernicus API and load it into the application.

The following steps are taken to load satellite images:

<br>

#### Download Files

Files are downloaded to the local MEDIA_SOURCE directory for a selected day or days and pollutants.

<br>

#### Load Database 

The downloaded files are processed to collect relevant data and load the image values into the local application database.  The database holds links to the source files with relevant parameters that describe what is in each file.  

<br>

#### Retrieve Satellite Images
 
 A view file contains the code necessary to retrieve satellite images using the database and the stored files.

<br>

## Rapid Start ....
To get going quickly:

Update daily data:

    python manage.py copernicus_load_daily_images
    python manage.py copernicus_load_db_from_files
    



Retrieve data:

    from .views import copernicus_views.py

    images_array, params_dict = get_satellite_images(year, month, day) 

Images array returned is 4-dimensional: (hours, levels, height, width).
The dictionary contains images information.

<br>


## Download Files
This process will download files for a selected day.

`python manage.py copernicus_load_daily_images`

available options:
- '-t', '--token' : Optional. A default token is used or a specific token can be designated with this option.
 
- '-d', '--target_dir': Optional. Defaults to the MEADIA_ROOT+'media'.

- '-c', '--category': List. default 'ANALYSIS'. FORECAST can also be added to list. e.g -c ANALYSIS FORECAST

- '-l', '--levels': default 'ALLLEVELS'. SURFACE can also be added to the list. e.g. -l ALLLEVELS SURFACE

- '-r', '--reference_time': Defaults to local date.  Specific days up to 30 days in the past can be used in iso format "YYYY-MM-DDT00:00:00Z"

<br>

## Load DataBase
Once files are downloaded, they must be added to the database.  The database will store the relevant parameters of the file along with a link to the file.

`python manage.py copernicus_load_db_from_files`

- '--root_path': Optional. Defaults to the MEADIA_ROOT+'media'.
- '--ext': Optional. Defaults to '.nc'

<br>

## Get Satellite Images
After files are downloaded and the database is populated, images can be retrieved for use in views.  An example of this function is in the following view file:

    /views/copernicus_views.py

<br>

To use this function import the view file:

    from .views import copernicus_views.py

<br>

The signature of the function is:

    get_satellite_images(year:int, month:int, day:int, pollutant_key:str, category:str, hours=[int], levels=[int], model='ENSEMBLE')  -> np.array, dict

<br>
    
    
 Returns images based on criteria along with a dictionary or parameters.

- year : Integer. The year from which to return pollution images. <br>

- month: Integer. The month from which to return pollution images. <br>

- day: Integer. The day from which to return pollution images. <br>

- pollutant_key: The key value used for pollutant. Available keys are found using:

    `import airpollution.static.airpollution.copernicus.CopernicusDataSource as copernicus_api`
    
    The following global variable contains a dictionary of the pollutants
    
    `copernicus_api.POLLUTANTS`
    
        POLLUTANTS = {
            'O3': {'pollutant_key': 'O3', 'pollutant': 'o3_conc', 'unit': 'micro g/m3'},
            'CO': {'pollutant_key': 'CO', 'pollutant': 'co_conc', 'unit': 'micro g/m3'},
            'NO2': {'pollutant_key': 'NO2', 'pollutant': 'no2_conc', 'unit': 'micro g/m3'},
            'SO2': {'pollutant_key': 'SO2', 'pollutant': 'so2_conc', 'unit': 'micro g/m3'},
            'PM25': {'pollutant_key': 'PM25', 'pollutant': 'pm2p5_conc', 'unit': 'micro g/m3'},
            'PM10': {'pollutant_key': 'PM10', 'pollutant': 'om10_conc', 'unit': 'micro g/m3'},
            'PANS': {'pollutant_key': 'PANS', 'pollutant': 'pans_conc', 'unit': 'micro g/m3'},
            'NMVOC': {'pollutant_key': 'NMVOC', 'pollutant': 'nmvoc_conc', 'unit': 'micro g/m3'},
            'NO': {'pollutant_key': 'NO', 'pollutant': 'no_conc', 'unit': 'micro g/m3'},
            'NH3': {'pollutant_key': 'NH3', 'pollutant': 'nh3_conc', 'unit': 'micro g/m3'},
            'BIRCH POLLEN': {'pollutant_key': 'BIRCHPOLLEN', 'pollutant': 'bpg_conc', 'unit': 'grains/m3'},
            'OLIVE POLLEN': {'pollutant_key': 'OLIVEPOLLEN', 'pollutant': 'opg_conc', 'unit': 'grains/m3'},
            'GRASS POLLEN': {'pollutant_key': 'GRASSPOLLEN', 'pollutant': 'gpg_conc', 'unit': 'grains/m3'},
            'RAGWEED POLLEN': {'pollutant_key': 'RAGWEEDPOLLEN', 'pollutant': 'rwpg_conc', 'unit': 'grains/m3'},
        }
    


- hours: Optional. Defaults to all available. [0-23] The hours in the day for which to return images <br>

- levels: Optional. Defaults to all available. The elevations for which to return images <br>

- category: 'ANALYSIS' or 'FORECAST' <br>

- model: Optional. Defaults to 'ENSEMBLE'. The Copernicus model <br>

### Returned Values
The function will return an np.array and a dictionary.

The numpy array is 4 dimensional:
(hours, levels, height, width)

The dictionary contains information about what is in the numpy array images.  Below are the keys with example values:

    {'description': 'O3 Air Pollutant ANALYSIS at 8 levels: ', 
    'category': 'ANALYSIS', 
    'pollutant_key': 'O3', 
    'pollutant': 'o3_conc', 
    'model': 'ENSEMBLE', 
    'bbox_minlon': 0.049987793, 
    'bbox_maxlon': 359.94998, 
    'bbox_minlat': 30.049995, 
    'bbox_maxlat': 69.95, 
    'levels': [0, 50, 250, 500, 1000, 2000, 3000, 5000], 
    'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], 
    'date': '2020-03-20', 
    'year': 2020, 
    'month': 3, 
    'day': 20, 
    'shape': (24, 8, 400, 700)}  

    



