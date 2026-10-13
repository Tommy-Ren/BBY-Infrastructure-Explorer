"""
Configuration and input schemas for the cleaning pipeline.
"""

import pathlib

import pandas as pd


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIRECTORY = PROJECT_ROOT / 'data' / 'raw'
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / 'data' / 'processed'

SCHOOL_PLACE_TYPE = 500
# Report snapshot expectation, overridable after review via --expected-school-count.
EXPECTED_SCHOOL_COUNT = 64
OUTPUT_CRS = 'EPSG:26910'
EARLIEST_SIGNAL_DATE = pd.Timestamp('1900-01-01', tz='UTC')
PLACES_COLUMNS = {'OBJECTID', 'PLACETYPE', 'DESCRIPTION', 'geometry'}
TRAFFIC_CALMING_REQUIRED_COLUMNS = {
    'OBJECTID', 'TYPE', 'INSTDATE', 'LOC', 'SERVSTAT', 'geometry'
}
TRAFFIC_SIGNAL_REQUIRED_COLUMNS = {
    'OBJECTID', 'UNITID', 'CONTROLCODE', 'INSTDATE', 'SERVSTAT', 'geometry'
}
INTERSECTION_REQUIRED_COLUMNS = {
    'OBJECTID', 'INTERSECTIONTYPE', 'CONTROLCODE', 'SIGNALKEY', 'STATUS',
    'STREETNAME1', 'STREETNAME2', 'geometry'
}
