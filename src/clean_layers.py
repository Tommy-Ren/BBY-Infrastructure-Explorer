"""
Transform raw Burnaby layers into analysis-ready GeoDataFrames.
"""

import pandas as pd

from clean_config import (
    EARLIEST_SIGNAL_DATE,
    EXPECTED_SCHOOL_COUNT,
    OUTPUT_CRS,
    SCHOOL_PLACE_TYPE,
)


def clean_schools(places):
    """
    Select schools, keep useful fields, and project coordinates into metres.
    """
    schools = places[places['PLACETYPE'] == SCHOOL_PLACE_TYPE].copy()
    schools = schools.rename(columns={
        'OBJECTID': 'school_id',
        'DESCRIPTION': 'school_name',
    })
    schools = schools[['school_id', 'school_name', 'geometry']]

    if len(schools) != EXPECTED_SCHOOL_COUNT:
        raise RuntimeError(
            f'Expected {EXPECTED_SCHOOL_COUNT} schools but found {len(schools)}.'
        )
    if schools['school_id'].isna().any() or schools['school_id'].duplicated().any():
        raise RuntimeError('School IDs are missing or duplicated.')
    if schools['school_name'].isna().any() or schools['school_name'].duplicated().any():
        raise RuntimeError('School names are missing or duplicated.')

    schools = schools.sort_values('school_name').reset_index(drop=True)
    return schools.to_crs(OUTPUT_CRS)


def clean_comparison_places(places, type_labels):
    """
    Keep all non-school public places as a reproducible comparison group.
    """
    comparison_places = places[places['PLACETYPE'] != SCHOOL_PLACE_TYPE].copy()
    comparison_places = comparison_places.rename(columns={
        'OBJECTID': 'place_id',
        'DESCRIPTION': 'place_name',
        'PLACETYPE': 'place_type_code',
    })
    comparison_places['place_type_code'] = (
        comparison_places['place_type_code'].astype('string')
    )
    comparison_places['place_type'] = (
        comparison_places['place_type_code'].map(type_labels)
    )
    comparison_places = comparison_places[[
        'place_id',
        'place_name',
        'place_type_code',
        'place_type',
        'geometry',
    ]]

    if (
        comparison_places['place_id'].isna().any()
        or comparison_places['place_id'].duplicated().any()
    ):
        raise RuntimeError('Comparison-place IDs are missing or duplicated.')
    if comparison_places['place_name'].isna().any():
        raise RuntimeError('Comparison-place names are missing.')
    if comparison_places['place_type'].isna().any():
        raise RuntimeError('Comparison-place type labels are missing.')

    comparison_places = comparison_places.sort_values(
        'place_name'
    ).reset_index(drop=True)
    return comparison_places.to_crs(OUTPUT_CRS)


def clean_traffic_calming(traffic_calming, type_labels):
    """
    Keep useful traffic-calming fields and decode documented type codes.
    """
    traffic_calming = traffic_calming.rename(columns={
        'OBJECTID': 'calming_id',
        'TYPE': 'calming_type_code',
        'LOC': 'location',
        'SERVSTAT': 'service_status',
    })
    traffic_calming['calming_type_code'] = (
        traffic_calming['calming_type_code'].astype('string')
    )
    traffic_calming['calming_type'] = (
        traffic_calming['calming_type_code'].map(type_labels)
    )

    unlabelled = (
        traffic_calming['calming_type'].isna()
        & traffic_calming['calming_type_code'].notna()
    )
    traffic_calming.loc[unlabelled, 'calming_type'] = (
        'Unlabelled code '
        + traffic_calming.loc[unlabelled, 'calming_type_code']
    )
    traffic_calming['calming_type'] = traffic_calming['calming_type'].fillna('Missing')
    traffic_calming['installation_date'] = pd.to_datetime(
        traffic_calming['INSTDATE'], unit='ms', utc=True, errors='coerce'
    )
    traffic_calming['location'] = traffic_calming['location'].astype('string')
    traffic_calming['service_status'] = (
        traffic_calming['service_status'].astype('string')
    )

    traffic_calming = traffic_calming[[
        'calming_id',
        'calming_type_code',
        'calming_type',
        'installation_date',
        'location',
        'service_status',
        'geometry',
    ]]
    if (
        traffic_calming['calming_id'].isna().any()
        or traffic_calming['calming_id'].duplicated().any()
    ):
        raise RuntimeError('Traffic-calming IDs are missing or duplicated.')

    traffic_calming = traffic_calming.sort_values('calming_id').reset_index(drop=True)
    return traffic_calming.to_crs(OUTPUT_CRS)


def clean_traffic_signals(traffic_signals):
    """
    Keep the traffic-signal fields needed for later distance analysis.
    """
    traffic_signals = traffic_signals.rename(columns={
        'OBJECTID': 'signal_id',
        'UNITID': 'unit_id',
        'CONTROLCODE': 'control_code',
        'SERVSTAT': 'service_status',
    })
    traffic_signals['installation_date'] = pd.to_datetime(
        traffic_signals['INSTDATE'], unit='ms', utc=True, errors='coerce'
    )
    traffic_signals['installation_date'] = traffic_signals[
        'installation_date'
    ].mask(traffic_signals['installation_date'] < EARLIEST_SIGNAL_DATE)
    for column in ['unit_id', 'control_code', 'service_status']:
        traffic_signals[column] = (
            traffic_signals[column].astype('string').str.strip().replace('', pd.NA)
        )

    traffic_signals = traffic_signals[[
        'signal_id',
        'unit_id',
        'control_code',
        'installation_date',
        'service_status',
        'geometry',
    ]]
    if (
        traffic_signals['signal_id'].isna().any()
        or traffic_signals['signal_id'].duplicated().any()
    ):
        raise RuntimeError('Traffic-signal IDs are missing or duplicated.')

    traffic_signals = traffic_signals.sort_values('signal_id').reset_index(drop=True)
    return traffic_signals.to_crs(OUTPUT_CRS)


def clean_intersections(intersections):
    """
    Keep intersection identifiers, street names, and source category codes.
    """
    intersections = intersections.rename(columns={
        'OBJECTID': 'intersection_id',
        'INTERSECTIONTYPE': 'intersection_type_code',
        'CONTROLCODE': 'control_code',
        'SIGNALKEY': 'signal_key',
        'STATUS': 'status',
        'STREETNAME1': 'street_name_1',
        'STREETNAME2': 'street_name_2',
    })
    for column in ['control_code', 'status', 'street_name_1', 'street_name_2']:
        intersections[column] = (
            intersections[column].astype('string').str.strip().replace('', pd.NA)
        )
    intersections['signal_key'] = intersections['signal_key'].astype('Int64')

    intersections = intersections[[
        'intersection_id',
        'intersection_type_code',
        'control_code',
        'signal_key',
        'status',
        'street_name_1',
        'street_name_2',
        'geometry',
    ]]
    if (
        intersections['intersection_id'].isna().any()
        or intersections['intersection_id'].duplicated().any()
    ):
        raise RuntimeError('Intersection IDs are missing or duplicated.')

    intersections = intersections.sort_values('intersection_id').reset_index(drop=True)
    return intersections.to_crs(OUTPUT_CRS)
