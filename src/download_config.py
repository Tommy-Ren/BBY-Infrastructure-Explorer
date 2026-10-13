"""
Configuration for downloading City of Burnaby ArcGIS data.
"""

import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / 'data' / 'raw'
OUTPUT_SPATIAL_REFERENCE = 4326
REQUEST_TIMEOUT = 60

LAYERS = {
    'places_of_interest': (
        'https://gis.burnaby.ca/arcgis/rest/services/'
        'OpenData/OpenData1/MapServer/1'
    ),
    'traffic_calming': (
        'https://gis.burnaby.ca/arcgis/rest/services/'
        'OpenData/OpenData5/MapServer/3'
    ),
    'traffic_signals': (
        'https://gis.burnaby.ca/arcgis/rest/services/'
        'OpenData/OpenData5/MapServer/1'
    ),
    'intersections': (
        'https://gis.burnaby.ca/arcgis/rest/services/'
        'OpenData/OpenData5/MapServer/5'
    ),
}
