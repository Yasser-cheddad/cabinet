
#WSGI config for cabinet project.

#It exposes the WSGI callable as a module-level variable named ``application``.

#For more information on this file, see
#https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/


import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cabinet.settings')

application = get_wsgi_application()
