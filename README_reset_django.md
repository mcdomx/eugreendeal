# Initialize/Reinitialize Django Setup

## 1) Stop The Server
Use crtl-c to stop the Django server if it is running.

## 2) Stop Docker and Remove Data Volume
If you are reinitializing, you need to stop Docker and remove the volume storing the application db.

- Navigate to eugreendeal/infrastructure

enter `docker-compose down`

Remove the volume with:
`docker volume rm infrastructure_database_data`

Do both at same time ... QUICK COPY/PASTE <br>
`docker-compose down; docker volume rm infrastructure_database_data`

## 3) Delete Migrations
Delete all the Django migrations from airpollution/migrations.
Leave the `__init__.py` file in place. 

## 4) Restart Docker
Make sure docker is running on your machine.

From the infrastrucure directory: <br>
`docker-compose up`

## 5) Setup PIPENV Shell
Navigate to eugreendeal.  Initial the pipenv shell: <br>
`pipenv shell`

Update the modules used in the project: <br>
`pipenv update`

Do both at same time ... QUICK COPY/PASTE <br>
`pipenv shell; pipenv update`

## 6) Migrate tables
COPY/PASTE <br>
`python manage.py makemigrations; python manage.py migrate` <br>

## 7) Setup Superuser
From eugreendeal directory: <br>
`python manage.py createsuperuser`

Create credentials as promoted.

## 8) Load Dummy Data

`python manage.py populate_db`