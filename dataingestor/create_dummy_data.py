import django
import os

from airpollution.management.commands.populate_db import Command

os.environ['DJANGO_SETTINGS_MODULE'] = 'eugreendeal.settings'
django.setup()

Command().create_some_dummy_data()


