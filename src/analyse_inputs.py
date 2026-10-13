"""
Read and validate cleaned spatial layers for coverage analysis.
"""

import geopandas as gpd

from analyse_config import (
    COMPARISON_PLACE_COLUMNS,
    EXPECTED_CRS,
    INTERSECTION_COLUMNS,
    SCHOOL_COLUMNS,
    TRAFFIC_CALMING_COLUMNS,
    TRAFFIC_SIGNAL_COLUMNS,
)


def read_spatial_data(input_directory):
    """
    Read the cleaned spatial layers needed for nearest-distance analysis.
    """
    schools_file = input_directory / 'schools.geojson'
    comparison_places_file = input_directory / 'comparison_places.geojson'
    traffic_calming_file = input_directory / 'traffic_calming.geojson'
    traffic_signals_file = input_directory / 'traffic_signals.geojson'
    intersections_file = input_directory / 'intersections.geojson'
    input_files = [
        schools_file,
        comparison_places_file,
        traffic_calming_file,
        traffic_signals_file,
        intersections_file,
    ]
    for input_file in input_files:
        if not input_file.exists():
            raise RuntimeError(f'Missing input file: {input_file}')

    schools = gpd.read_file(schools_file)
    comparison_places = gpd.read_file(comparison_places_file)
    traffic_calming = gpd.read_file(traffic_calming_file)
    traffic_signals = gpd.read_file(traffic_signals_file)
    intersections = gpd.read_file(intersections_file)
    missing_school_columns = SCHOOL_COLUMNS - set(schools.columns)
    missing_comparison_columns = COMPARISON_PLACE_COLUMNS - set(
        comparison_places.columns
    )
    missing_calming_columns = TRAFFIC_CALMING_COLUMNS - set(
        traffic_calming.columns
    )
    missing_signal_columns = TRAFFIC_SIGNAL_COLUMNS - set(
        traffic_signals.columns
    )
    missing_intersection_columns = INTERSECTION_COLUMNS - set(
        intersections.columns
    )
    if missing_school_columns:
        raise RuntimeError(
            f'Missing school columns: {sorted(missing_school_columns)}'
        )
    if missing_comparison_columns:
        raise RuntimeError(
            'Missing comparison-place columns: '
            f'{sorted(missing_comparison_columns)}'
        )
    if missing_calming_columns:
        raise RuntimeError(
            'Missing traffic-calming columns: '
            f'{sorted(missing_calming_columns)}'
        )
    if missing_signal_columns:
        raise RuntimeError(
            f'Missing traffic-signal columns: {sorted(missing_signal_columns)}'
        )
    if missing_intersection_columns:
        raise RuntimeError(
            'Missing intersection columns: '
            f'{sorted(missing_intersection_columns)}'
        )
    if (
        schools.empty
        or comparison_places.empty
        or traffic_calming.empty
        or traffic_signals.empty
        or intersections.empty
    ):
        raise RuntimeError('The spatial input data must not be empty.')
    if (
        schools.crs is None
        or comparison_places.crs is None
        or traffic_calming.crs is None
        or traffic_signals.crs is None
        or intersections.crs is None
    ):
        raise RuntimeError('The spatial input data must have a CRS.')
    if (
        schools.crs != traffic_calming.crs
        or schools.crs != comparison_places.crs
        or schools.crs != traffic_signals.crs
        or schools.crs != intersections.crs
        or schools.crs.to_string() != EXPECTED_CRS
    ):
        raise RuntimeError(f'Input data must use {EXPECTED_CRS}.')
    return (
        schools,
        comparison_places,
        traffic_calming,
        traffic_signals,
        intersections,
    )
