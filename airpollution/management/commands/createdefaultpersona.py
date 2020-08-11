import logging

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Command class to create a default persona when initializing database for the first time
    """

    args = 'no args required'
    help = 'Create a default persona to initialize persona groups'

    def handle(self, *args, **options):
        logger = logging.getLogger("createdefaultpersona")
        logger.setLevel(level=options.get('verbosity', logging.ERROR))
        if Group.objects.count() > 0:
            logger.warning('Skipping creating default persona with name. Since Personas already exist in database.')
        else:
            logger.info('Creating default persona with name: DefaultPersona')
            group = Group.objects.create(name='DefaultPersona', description='Default Persona created at startup')
            group.save()
            logger.info('Default persona created')
