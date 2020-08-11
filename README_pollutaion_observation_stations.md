# Pollution Observations
For target measurement, pollution is measured from ground observation stations.  These stations are scattered throughout Europe with new stations are created on a regular basis.  At the time the document was created, approximately 7000 observation stations were delivering data.

Observation readings are collected at irregular intervals by stations.  The delivered data includes information about the time observations are collected from each station for each pollutant.  Not all stations collect all pollutants.

In order to associate the station's location with it's data, information about the stations is also collected in this process.

A single management function is created to update the stations and collect observation readings.

The following processes are described in this document:

<br>

#### Update Database

The process contains two steps.  First, updated meta-data on the stations is collected.  Next, observation data is copied into the local database.
 

<br>

#### Get Station Data
 
 Information on stations can be collected without readings information.
 
<br>


#### Get Pollution Observation Data
 
 Information about pollution readings is collected.  As this information is specific to regions and time periods, there are several parameters necessary to target the information required.
 
<br>


## Rapid Start ....
To get going quickly:

Update daily data:

    python manage.py load_eea_station_data

Retrieve data:

    from .views import eea_station_views

    stations_dictionary  = get_stations(request, station_name: str = None)
    
    obervations_dictionary = get_pollution_observations(start_date, end_date, time_type, country_code, nuts_region, pollutant)

<br>

## Updated DataBase
This process will download files for a selected day.

`python manage.py load_eea_station_data`

A progress bar will show the progress of loads.  Loading all the data for all stations for a single year is already time consuming.  Avoid doing this for multiple years, if possible.

available options:
- '--year_from' : Required. The start year from which to collect data.
 
- '--year_to': Required. The end year (inclusive) from which to collect data.

- '--country_code': String. Optional.  Default = None. If none provided, all countries will be included.

- '--pollutant': String.  Optional.  Default = None. If blank, all pollutants are collected.

- '--station': String. Optional Defaults to = None.  If None, all stations are selected.  Station must match station code.

- '--meta_url': String. Optional. Defaults to source location.  Don't use this unless you know how the url data fits into the supporting functions and databases.  

- '--meta_targetdir': String. Optional Defaults to application default for this purpose.  No need to change this.  This is where the file is downloaded before it is used to load data into the database.

- '--load_from_file': String. Optional.  By default, a new file is downloaded each time the management function is called.  The new download can be skipped and the locally stored data from prior days can be used instead.  Setting this parameter to True will avoid a new download and use the locally stored file instead.  This will go faster, but you risk having observation data ignored for newly added stations.  When this option is True, the file will be loaded from the `--meta_targetdir` directory.


<br>

## Get Station Data
After data is updated, station dataa can be extracted.  Functions to do this are in the view file:

    /views/eea_station_views.py

The following function will retrieve the data:

    def get_stations(request, station_name: str = None)
    
This will return a JsonResponse object.  

Using the station name will limit the response to a single station.  Below is an example of a formatted response:

    {
    "STA-FR16066": {
    "country_code": "FR",
    "air_quality_network": "NET-FR075A",
    "air_quality_station_eoicode": "FR16066",
    "air_quality_station_natcode": "FR16066",
    "projection": "EPSG:4979",
    "longitude": 7.309075,
    "latitude": 47.73741699946572,
    "altitude": 267,
    "air_quality_station_area": "urban"
    }
    }


## Get Pollution Observation Data
Data can be collected for various levels of pollution data.

    def get_pollution_observations(start_date, end_date, time_type, country_code, nuts_region, pollutant) -> dict

This function is available in the view:

    pollution_observations_views.py

This view can be imported as:

    from .views import pollution_observations_views

The following variables are supported:
- start_date: str   : 8-digit date 'YYYYMMDD'
- end_date: str     : 8-digit date 'YYYYMMDD' (inclusive)
- time_type         : see link below for details. *1)
<br>-> 'hourly' - all available hours for the day
<br>-> 'day_mean' - a mean value for all available and valid hours for each day
<br>-> 'rolling' - An 8-hour rolling mean for the day. Each hour value provided is the mean of that hour and the previous 7.

- country_code: str : the 2-character country code. All are selected, if None.
- nuts_region: str  : the nuts region code.  All NUTS levels are supported. All are selected if None.
- station_code: str : station code from which to collect data
- pollutant: str    : the pollutant code (all are retrieved if NONE)


*1) https://www.eionet.europa.eu/aqportal/doc/ETC_Aggregation_v0.8.2_final.pdf <br>


Response:

A dictionary is returned with the following structure:

{ 'fr' :
        { 'STA-FR16066' :
                            { 'YYYYMMDDHH' :
                                             { 'c6h6' : 50000,
                                               'no'   : 50000
                                               'co'   : 50000
                                               }
                            },
          'STA-FR16067' :
                            { 'YYYYMMDDHH' :
                                             { 'c6h6' : 49000,
                                               'pm25' : 49000
                                               'no3'   : 49000
                                               }
                            },              
        }
}


## Load Pollutions Observations to Database
A manage.py command is used to load data.  Data loads are flexible and have several options, but the simplest version of the command will choose to load the last 7-days of data.

If new data is request that already exists in the database, the existing database data will first be deleted and then replaced by the newest downloaded data.  This is replaced instead of updated to accommodate changed data from the EEA.  The same delete/reload rule applies if loading yearly data.

Each data update request will start with refreshing the list of EEA observation stations to ensure that new data from new stations can be accommodated in the database.  Each station has its own master data record that must first be created before loading observation data into the database.

The base command for the dataload is:

`python manage.py load_eea_station_data <see options below>`

`--filename` - If you want to upload new stations from a custom file include that filename. <br> 
Usage: `--fillename PanEuropean_metadata.csv`.<br>
This is the default file name which is newly downloaded if this option is not selected.  

`--year_from` and `--year_to` - If loading entire years at a time, select a 4-digit start year and ending year.  Will first erase data for the year and before downloading and reloading.  This option is ignored if the `--since_date` option is selected.

`--since_date` - The date from which all records should be loaded up until the current date.  Format YYYY-MM-DD.  This option supercedes `--year_from` and `--year_to`.

`--country_codes` - A list of country codes that should be laoded.  Space-delimited list of any combination of EU country codes.<br>

`--pollutants` - A list of pollutant keys that should be loaded.  Space-delimited list of any combination of the following: <br> `PM25 PM10 CO SO2 O3 NO2`. <br>
 
`--stations` - Stations for which data should be loaded.
Can include a space-delimited list of station codes.  No quotes are needed around station text code fields.
 
`--skip_stations` - Assigning a `1` will skip the process of downloading and updated base station meta-data.<br>
Usage: `--skip_stations 1`
