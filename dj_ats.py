import os
import django
from django.conf import settings
from django.urls import path
from django.http import JsonResponse
from django.db import models
import requests

# ------------------- Django Setup -------------------
BASE_DIR = os.path.dirname(__file__)

settings.configure(
    DEBUG=True,
    SECRET_KEY='secret',
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    MIDDLEWARE=[],
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.sessions',
        '__main__',  # register models in this file
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'aircraft_data',
            'USER': 'aircraft_data_user',
            'PASSWORD': '6PZIW63RoeCj5cthsEPTZaCeSZm2ZQEQ',
            'HOST': 'dpg-d1t092emcj7s73b0mhlg-a.oregon-postgres.render.com',
            'PORT': '5432',
        }
    },
)

django.setup()

# ------------------- Model -------------------
class AircraftData(models.Model):
    icao24 = models.CharField(max_length=10, null=True)
    callsign = models.CharField(max_length=10, null=True)
    origin_country = models.CharField(max_length=50, null=True)
    time_position = models.BigIntegerField(null=True)
    last_contact = models.BigIntegerField(null=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    baro_altitude = models.FloatField(null=True)
    on_ground = models.BooleanField(default=False)
    velocity = models.FloatField(null=True)
    true_track = models.FloatField(null=True)
    vertical_rate = models.FloatField(null=True)
    geo_altitude = models.FloatField(null=True)
    squawk = models.CharField(max_length=10, null=True)
    spi = models.BooleanField(default=False)
    position_source = models.IntegerField(null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = '__main__'

# ------------------- View -------------------
def get_aircrafts(request):
    try:
        res = requests.get("https://opensky-network.org/api/states/all", timeout=5)
        res.raise_for_status()
        data = res.json()

        aircrafts = [{
            'icao24': s[0], 'callsign': s[1], 'origin_country': s[2],
            'longitude': s[5], 'latitude': s[6], 'baro_altitude': s[7],
            'geo_altitude': s[13], 'velocity': s[9], 'on_ground': s[8]
        } for s in data.get("states", [])[:10]]

        return JsonResponse({'source': 'opensky', 'aircrafts': aircrafts})

    except Exception as e:
        fallback = AircraftData.objects.order_by('-recorded_at')[:10]
        aircrafts = [{
            'icao24': a.icao24, 'callsign': a.callsign, 'origin_country': a.origin_country,
            'longitude': a.longitude, 'latitude': a.latitude,
            'baro_altitude': a.baro_altitude, 'geo_altitude': a.geo_altitude,
            'velocity': a.velocity, 'on_ground': a.on_ground
        } for a in fallback]
        return JsonResponse({'source': 'database', 'aircrafts': aircrafts})

# ------------------- URL -------------------
urlpatterns = [
    path('aircrafts/', get_aircrafts),
]

# ------------------- Run Server -------------------
if __name__ == "__main__":
    import sys
    from django.core.management import execute_from_command_line

    # For DB migrations only on first run
    if 'runserver' in sys.argv:
        execute_from_command_line(['', 'makemigrations', '__main__'])
        execute_from_command_line(['', 'migrate'])

    execute_from_command_line(sys.argv)
