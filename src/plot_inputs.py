"""
Read and validate spatial and tabular inputs used by project figures.
"""

import geopandas as gpd
import pandas as pd

from plot_config import (
    COMPARISON_DISTANCE_COLUMNS,
    COVERAGE_SUMMARY_COLUMNS,
    EXPECTED_CRS,
    INTERSECTION_COLUMNS,
    SCHOOL_COLUMNS,
    SCHOOL_DISTANCE_COLUMNS,
    TRAFFIC_CALMING_COLUMNS,
)


def read_map_data(input_directory):
    """
    Read and validate the processed layers used in the overview map.
    """
    schools_file = input_directory / 'schools.geojson'
    traffic_calming_file = input_directory / 'traffic_calming.geojson'
    intersections_file = input_directory / 'intersections.geojson'
    for input_file in [schools_file, traffic_calming_file, intersections_file]:
        if not input_file.exists():
            raise RuntimeError(f'Missing input file: {input_file}')

    schools = gpd.read_file(schools_file)
    traffic_calming = gpd.read_file(traffic_calming_file)
    intersections = gpd.read_file(intersections_file)
    missing_school_columns = SCHOOL_COLUMNS - set(schools.columns)
    missing_calming_columns = TRAFFIC_CALMING_COLUMNS - set(
        traffic_calming.columns
    )
    missing_intersection_columns = INTERSECTION_COLUMNS - set(
        intersections.columns
    )
    if missing_school_columns:
        raise RuntimeError(f'Missing school columns: {sorted(missing_school_columns)}')
    if missing_calming_columns:
        raise RuntimeError('Missing traffic-calming columns: ' f'{sorted(missing_calming_columns)}')
    if missing_intersection_columns:
        raise RuntimeError('Missing intersection columns: ' f'{sorted(missing_intersection_columns)}')
    if schools.empty or traffic_calming.empty or intersections.empty:
        raise RuntimeError('Map input layers must not be empty.')
    if (schools.crs is None or traffic_calming.crs is None or intersections.crs is None):
        raise RuntimeError('Map input layers must have a CRS.')
    if (schools.crs != traffic_calming.crs or schools.crs != intersections.crs or schools.crs.to_string() != EXPECTED_CRS):
        raise RuntimeError(f'Map input layers must use {EXPECTED_CRS}.')
    return schools, traffic_calming, intersections


def read_distance_data(table_directory):
    """
    Read the school and comparison-place nearest-distance tables.
    """
    school_file = table_directory / 'school_nearest_traffic_calming.csv'
    comparison_file = table_directory / 'comparison_nearest_traffic_calming.csv'
    for input_file in [school_file, comparison_file]:
        if not input_file.exists():
            raise RuntimeError(f'Missing input file: {input_file}')

    school_distances = pd.read_csv(school_file)
    comparison_distances = pd.read_csv(comparison_file)
    for name, distances, required_columns in [
        ('School', school_distances, SCHOOL_DISTANCE_COLUMNS),
        (
            'Comparison-place',
            comparison_distances,
            COMPARISON_DISTANCE_COLUMNS,
        ),
    ]:
        missing_columns = required_columns - set(distances.columns)
        if missing_columns:
            raise RuntimeError(f'Missing {name.lower()} columns: {sorted(missing_columns)}')
        if distances.empty:
            raise RuntimeError(f'{name} distance data must not be empty.')
        if distances['nearest_calming_distance_m'].isna().any():
            raise RuntimeError(f'{name} distance data contains missing values.')
        if (distances['nearest_calming_distance_m'] < 0).any():
            raise RuntimeError(f'{name} distance data contains negative values.')
    return school_distances, comparison_distances


def read_coverage_summary(table_directory):
    """
    Read and validate the school coverage summary table.
    """
    input_file = table_directory / 'traffic_calming_coverage_summary.csv'
    if not input_file.exists():
        raise RuntimeError(f'Missing input file: {input_file}')

    coverage = pd.read_csv(input_file)
    missing_columns = COVERAGE_SUMMARY_COLUMNS - set(coverage.columns)
    if missing_columns:
        raise RuntimeError(f'Missing coverage columns: {sorted(missing_columns)}')
    if coverage.empty:
        raise RuntimeError('Coverage summary must not be empty.')
    if coverage[list(COVERAGE_SUMMARY_COLUMNS)].isna().any().any():
        raise RuntimeError('Coverage summary contains missing values.')
    if not coverage['coverage_percent'].between(0, 100).all():
        raise RuntimeError('Coverage percentages must be between 0 and 100.')
    if not (
        coverage['schools_with_feature']
        + coverage['schools_without_feature']
        == coverage['total_schools']
    ).all():
        raise RuntimeError('Coverage school counts do not add to the total.')
    return coverage.sort_values('distance_m').reset_index(drop=True)
