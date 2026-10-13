"""
Configuration and schemas for coverage analysis.
"""

import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIRECTORY = PROJECT_ROOT / 'data' / 'processed'
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / 'output' / 'tables'

EXPECTED_CRS = 'EPSG:26910'
SCHOOL_COLUMNS = {'school_id', 'school_name', 'geometry'}
COMPARISON_PLACE_COLUMNS = {
    'place_id', 'place_name', 'place_type', 'geometry'
}
TRAFFIC_CALMING_COLUMNS = {
    'calming_id', 'calming_type', 'geometry'
}
TRAFFIC_SIGNAL_COLUMNS = {
    'signal_id', 'unit_id', 'service_status', 'geometry'
}
INTERSECTION_COLUMNS = {
    'intersection_id', 'intersection_type_code', 'street_name_1',
    'street_name_2', 'geometry'
}
REMOVED_SIGNAL_STATUS = 'RMVD'
COVERAGE_DISTANCES_M = [100, 250, 500]
