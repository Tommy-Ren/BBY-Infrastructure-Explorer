"""
Read and validate raw Burnaby spatial layers and metadata.
"""

import json

import geopandas as gpd

from clean_config import (
    INTERSECTION_REQUIRED_COLUMNS,
    PLACES_COLUMNS,
    TRAFFIC_CALMING_REQUIRED_COLUMNS,
    TRAFFIC_SIGNAL_REQUIRED_COLUMNS,
)


def read_places(input_directory):
    """
    Read the Places of Interest file and validate the required input fields.
    """
    input_file = input_directory / 'places_of_interest.geojson'
    if not input_file.exists():
        raise RuntimeError(f'Missing input file: {input_file}')

    places = gpd.read_file(input_file)
    missing_columns = PLACES_COLUMNS - set(places.columns)
    if missing_columns:
        raise RuntimeError(f'Missing required columns: {sorted(missing_columns)}')
    if places.crs is None:
        raise RuntimeError('Places of Interest has no coordinate reference system.')
    if places.geometry.isna().any() or places.geometry.is_empty.any():
        raise RuntimeError('Places of Interest contains missing or empty geometry.')
    if not places.geometry.is_valid.all():
        raise RuntimeError('Places of Interest contains invalid geometry.')
    return places


def read_place_type_labels(input_directory):
    """
    Read the official labels for Places of Interest type codes.
    """
    metadata_file = input_directory / 'places_of_interest.metadata.json'
    if not metadata_file.exists():
        raise RuntimeError(f'Missing metadata file: {metadata_file}')

    with metadata_file.open(encoding='utf-8') as metadata_stream:
        metadata = json.load(metadata_stream)
    type_information = metadata['drawingInfo']['renderer']['uniqueValueInfos']
    return {
        str(item['value']): item['label']
        for item in type_information
    }


def read_traffic_calming(input_directory):
    """
    Read traffic-calming features and their official type labels.
    """
    input_file = input_directory / 'traffic_calming.geojson'
    metadata_file = input_directory / 'traffic_calming.metadata.json'
    if not input_file.exists():
        raise RuntimeError(f'Missing input file: {input_file}')
    if not metadata_file.exists():
        raise RuntimeError(f'Missing metadata file: {metadata_file}')

    traffic_calming = gpd.read_file(input_file)
    missing_columns = TRAFFIC_CALMING_REQUIRED_COLUMNS - set(traffic_calming.columns)
    if missing_columns:
        raise RuntimeError(f'Missing required columns: {sorted(missing_columns)}')
    if traffic_calming.crs is None:
        raise RuntimeError('Traffic-calming data has no coordinate reference system.')
    if traffic_calming.geometry.isna().any() or traffic_calming.geometry.is_empty.any():
        raise RuntimeError('Traffic-calming data contains missing or empty geometry.')
    if not traffic_calming.geometry.is_valid.all():
        raise RuntimeError('Traffic-calming data contains invalid geometry.')

    with metadata_file.open(encoding='utf-8') as metadata_stream:
        metadata = json.load(metadata_stream)
    type_information = metadata['drawingInfo']['renderer']['uniqueValueInfos']
    type_labels = {
        str(item['value']): item['label']
        for item in type_information
    }
    return traffic_calming, type_labels


def read_traffic_signals(input_directory):
    """
    Read traffic signals and validate the required input fields.
    """
    input_file = input_directory / 'traffic_signals.geojson'
    if not input_file.exists():
        raise RuntimeError(f'Missing input file: {input_file}')

    traffic_signals = gpd.read_file(input_file)
    missing_columns = TRAFFIC_SIGNAL_REQUIRED_COLUMNS - set(traffic_signals.columns)
    if missing_columns:
        raise RuntimeError(f'Missing required columns: {sorted(missing_columns)}')
    if traffic_signals.crs is None:
        raise RuntimeError('Traffic signals have no coordinate reference system.')
    if traffic_signals.geometry.isna().any() or traffic_signals.geometry.is_empty.any():
        raise RuntimeError('Traffic signals contain missing or empty geometry.')
    if not traffic_signals.geometry.is_valid.all():
        raise RuntimeError('Traffic signals contain invalid geometry.')
    return traffic_signals


def read_intersections(input_directory):
    """
    Read intersections and validate the required input fields.
    """
    input_file = input_directory / 'intersections.geojson'
    if not input_file.exists():
        raise RuntimeError(f'Missing input file: {input_file}')

    intersections = gpd.read_file(input_file)
    missing_columns = INTERSECTION_REQUIRED_COLUMNS - set(intersections.columns)
    if missing_columns:
        raise RuntimeError(f'Missing required columns: {sorted(missing_columns)}')
    if intersections.crs is None:
        raise RuntimeError('Intersections have no coordinate reference system.')
    if intersections.geometry.isna().any() or intersections.geometry.is_empty.any():
        raise RuntimeError('Intersections contain missing or empty geometry.')
    if not intersections.geometry.is_valid.all():
        raise RuntimeError('Intersections contain invalid geometry.')
    return intersections
