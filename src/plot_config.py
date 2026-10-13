"""
Configuration and input schemas for project figures.
"""

import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SPATIAL_DIRECTORY = PROJECT_ROOT / 'data' / 'processed'
DEFAULT_TABLE_DIRECTORY = PROJECT_ROOT / 'output' / 'tables'
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / 'output' / 'figures'

EXPECTED_CRS = 'EPSG:26910'
SCHOOL_COLUMNS = {'school_id', 'school_name', 'geometry'}
TRAFFIC_CALMING_COLUMNS = {'calming_id', 'calming_type', 'geometry'}
INTERSECTION_COLUMNS = {'intersection_id', 'geometry'}
SCHOOL_DISTANCE_COLUMNS = {'school_name', 'nearest_calming_distance_m'}
COMPARISON_DISTANCE_COLUMNS = {'place_name', 'nearest_calming_distance_m'}
COVERAGE_SUMMARY_COLUMNS = {
    'distance_m', 'total_schools', 'schools_with_feature',
    'schools_without_feature', 'coverage_percent'
}
PCA_SCORE_COLUMNS = {'school_id', 'school_name', 'pc1', 'pc2'}
CLUSTER_ASSIGNMENT_COLUMNS = {'school_id', 'school_name', 'cluster'}
PCA_VARIANCE_COLUMNS = {'component', 'explained_variance_ratio'}
LOW_COVERAGE_SCHOOL_COUNT = 12
