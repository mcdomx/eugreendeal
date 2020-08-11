#!/bin/bash
cd /app/ || exit
#python manage.py makemigrations
python manage.py migrate

echo $WORKSPACE
if [ -z "$WORKSPACE" ] || [ "$WORKSPACE" != "PROD" ]
then
      python manage.py runserver 0.0.0.0:8000
else
      gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 600 eugreendeal.wsgi
fi

