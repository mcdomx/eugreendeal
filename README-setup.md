# EU Green Deal Reporting

### Setup instructions

* **Python** >=3.7 : Install any version greater than or equal to python 3.7. You can use anaconda distribution since
it has prebuilt packages required to install psycopg2
* **Install libspatialindex-dev** : ``brew install spatialindex`` works on a mac (you can use apt-get as well)
* **Install psycopg2** : Verify psycopg2 is installed.
* **Docker (Optional)** : To run your local postgres database, you could either install a local postgres instance.
Or you could pull a docker image. If you go by the docker way (Follow only step 4, if you are using docker hub 
desktop and ignore rest of the steps) :
    1. cd infrastructure
    2. Start postgres docker: docker-compose up -d
    3. Check if postgres started without any errors: docker-compose logs
    4. Get the IP address of your local docker environment: 
        * If you are using docker hub desktop: Get the IP from docker hub UI
        * If you are using docker-machine: Run docker-machine env and note down the IP under DOCKER_HOST
    5. To bring postgres down (Optinal): docker-compose down
* **Postgres** : Open source code and replace the IP address next to 'HOST' under DATABASES in 
eugreendeal/settings.py . This would be either your docker machine IP address (if postgres is installed using docker) 
or localhost (if postgres is installed locally on your machine). If postgres is installed locally (not using docker),
then you would need to create the database with name and credentials mentioned under infrastructure/docker-compose.yml  
       
* **Django setup** 
	* pip install pipenv
	* cd eugreendeal
	* pipenv install
	* python manage.py makemigrations
	* python manage.py migrate
	* python manage.py populate_db
	* python manage.py createsuperuser 
	* python manage.py runserver

* Default App URL: http://localhost:8000
* Default Admin URL: http://localhost:8000/superadmin

* **Django Docker setup** : The optional step mentioned above also includes the EU Green deal server as a part of the 
docker-compose.yml file. If you are using a postgres DB of your own which is not instantiated using the docker 
environment, you need to configure the same in docker-compose.yml. You should configure the host, username and password 
under the service eugdweb.
If you are willing to rebuild the eugdserver container:
    * Make sure you have docker command line installed.
    * docker build -t eugdserver .
And that's it.    
App docker URL: http://<docker-machine-ip>:8000

If you only want to run the postgres database locally, you can use the following command to selectively run the database service only from the docker-compose file:

`docker-compose up -d db`

### **Tests**
* coverage run manage.py test --keepdb
* coverage html --include=../eugreendeal/airpollution/* --omit "../eugreendeal/airpollution/views/*,../eugreendeal/airpollution/management/*"

 

 
