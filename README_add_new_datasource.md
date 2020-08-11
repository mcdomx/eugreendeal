# Adding a New Datasource
Adding a new datasource requires a few steps.

1. Create a model <br>
Save the model in the `models/` directory. 

2. Add the model to `admin.py`
<br>
run `python manage.py makemigrations` and `python manage.py migrate`

3. Create a new `DataSource` class <br>
Create a new class that inherits from `dataingestor/DataSource.py`. This function requires a few implemented functions, of which, `load_data` is the more important.

4. Create a new management function <br>
Located in `management/commands/`.  This function should call the `load_data()` function in the new DataSource class saved in `/dataingestor/`

5. Create API to access data

