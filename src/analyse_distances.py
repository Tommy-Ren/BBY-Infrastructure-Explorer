"""
Calculate nearest-feature distances and compare distance distributions.
"""

import geopandas as gpd
import pandas as pd
from scipy import stats

from analyse_config import COVERAGE_DISTANCES_M, REMOVED_SIGNAL_STATUS


def nearest_traffic_calming(schools, traffic_calming):
    """
    Find the closest traffic-calming feature to every school
    """
    calming_columns = ['calming_id', 'calming_type', 'geometry']
    nearest = gpd.sjoin_nearest(
        schools,
        traffic_calming[calming_columns],
        how='left',
        distance_col='nearest_calming_distance_m',
    )
    nearest = nearest.sort_values([
        'school_id', 'nearest_calming_distance_m', 'calming_id'
    ])
    nearest = nearest.drop_duplicates('school_id')
    nearest = nearest.rename(columns={
        'calming_id': 'nearest_calming_id',
        'calming_type': 'nearest_calming_type',
    })
    nearest = nearest[[
        'school_id',
        'school_name',
        'nearest_calming_id',
        'nearest_calming_type',
        'nearest_calming_distance_m',
    ]]

    if len(nearest) != len(schools):
        raise RuntimeError('Not every school has one nearest traffic-calming feature')
    if nearest['nearest_calming_id'].isna().any():
        raise RuntimeError('At least one school has no nearest traffic-calming feature')
    if (nearest['nearest_calming_distance_m'] < 0).any():
        raise RuntimeError('Nearest-feature distances must not be negative')

    return nearest.sort_values('school_name').reset_index(drop=True)


def nearest_comparison_traffic_calming(comparison_places, traffic_calming):
    """
    Find the closest traffic-calming feature to every comparison place.
    """
    calming_columns = ['calming_id', 'calming_type', 'geometry']
    nearest = gpd.sjoin_nearest(
        comparison_places,
        traffic_calming[calming_columns],
        how='left',
        distance_col='nearest_calming_distance_m',
    )
    nearest = nearest.sort_values([
        'place_id', 'nearest_calming_distance_m', 'calming_id'
    ])
    nearest = nearest.drop_duplicates('place_id')
    nearest = nearest.rename(columns={
        'calming_id': 'nearest_calming_id',
        'calming_type': 'nearest_calming_type',
    })
    nearest = nearest[[
        'place_id',
        'place_name',
        'place_type',
        'nearest_calming_id',
        'nearest_calming_type',
        'nearest_calming_distance_m',
    ]]

    if len(nearest) != len(comparison_places):
        raise RuntimeError(
            'Not every comparison place has one nearest traffic-calming feature.'
        )
    if nearest['nearest_calming_id'].isna().any():
        raise RuntimeError(
            'At least one comparison place has no nearest traffic-calming feature.'
        )
    if (nearest['nearest_calming_distance_m'] < 0).any():
        raise RuntimeError('Nearest-feature distances must not be negative.')

    return nearest.sort_values('place_name').reset_index(drop=True)


def add_comparison_coverage_flags(comparison_nearest):
    """
    Mark whether each comparison place has a feature within each threshold.
    """
    distance_column = 'nearest_calming_distance_m'
    if distance_column not in comparison_nearest.columns:
        raise RuntimeError(
            f'Missing comparison-place distance column: {distance_column}'
        )
    if comparison_nearest[distance_column].isna().any():
        raise RuntimeError('Comparison-place distances contain missing values.')

    coverage = comparison_nearest.copy()
    for distance_m in COVERAGE_DISTANCES_M:
        coverage[f'covered_{distance_m}m'] = (
            coverage[distance_column] <= distance_m
        )
    return coverage


def compare_nearest_calming_distances(school_nearest, comparison_nearest):
    """
    Compare school and comparison-place distances with a two-sided U test.
    """
    school_distances = school_nearest['nearest_calming_distance_m']
    comparison_distances = comparison_nearest['nearest_calming_distance_m']
    if school_distances.isna().any() or comparison_distances.isna().any():
        raise RuntimeError('Nearest-distance samples contain missing values.')
    if school_distances.empty or comparison_distances.empty:
        raise RuntimeError('Nearest-distance samples must not be empty.')

    test_result = stats.mannwhitneyu(
        school_distances,
        comparison_distances,
        alternative='two-sided',
    )
    rank_biserial = (
        2 * test_result.statistic
        / (len(school_distances) * len(comparison_distances))
        - 1
    )
    comparison = pd.DataFrame([{
        'test': 'Mann-Whitney U',
        'alternative': 'two-sided',
        'school_n': len(school_distances),
        'school_mean_m': school_distances.mean(),
        'school_median_m': school_distances.median(),
        'comparison_n': len(comparison_distances),
        'comparison_mean_m': comparison_distances.mean(),
        'comparison_median_m': comparison_distances.median(),
        'median_difference_m': (
            school_distances.median() - comparison_distances.median()
        ),
        'u_statistic': test_result.statistic,
        'p_value': test_result.pvalue,
        'rank_biserial': rank_biserial,
    }])
    distance_columns = [
        'school_mean_m',
        'school_median_m',
        'comparison_mean_m',
        'comparison_median_m',
        'median_difference_m',
    ]
    comparison[distance_columns] = comparison[distance_columns].round(3)
    comparison['rank_biserial'] = comparison['rank_biserial'].round(3)
    return comparison


def nearest_traffic_signals(schools, traffic_signals):
    """
    Find the closest non-removed traffic signal to schools
    """
    traffic_signals = traffic_signals[
        traffic_signals['service_status'] != REMOVED_SIGNAL_STATUS
    ].copy()
    signal_columns = ['signal_id', 'unit_id', 'geometry']
    nearest = gpd.sjoin_nearest(
        schools,
        traffic_signals[signal_columns],
        how='left',
        distance_col='nearest_signal_distance_m',
    )
    nearest = nearest.sort_values([
        'school_id', 'nearest_signal_distance_m', 'signal_id'
    ])
    nearest = nearest.drop_duplicates('school_id')
    nearest = nearest.rename(columns={
        'signal_id': 'nearest_signal_id',
        'unit_id': 'nearest_signal_unit_id',
    })
    nearest = nearest[[
        'school_id',
        'school_name',
        'nearest_signal_id',
        'nearest_signal_unit_id',
        'nearest_signal_distance_m',
    ]]

    if len(nearest) != len(schools):
        raise RuntimeError('Not every school has one nearest traffic signal.')
    if nearest['nearest_signal_id'].isna().any():
        raise RuntimeError('At least one school has no nearest traffic signal.')
    if (nearest['nearest_signal_distance_m'] < 0).any():
        raise RuntimeError('Nearest-signal distances must not be negative.')

    return nearest.sort_values('school_name').reset_index(drop=True)


def nearest_intersections(schools, intersections):
    """
    Find the closest intersection to schools.
    """
    intersection_columns = [
        'intersection_id',
        'intersection_type_code',
        'street_name_1',
        'street_name_2',
        'geometry',
    ]
    nearest = gpd.sjoin_nearest(
        schools,
        intersections[intersection_columns],
        how='left',
        distance_col='nearest_intersection_distance_m',
    )
    nearest = nearest.sort_values([
        'school_id', 'nearest_intersection_distance_m', 'intersection_id'
    ])
    nearest = nearest.drop_duplicates('school_id')
    nearest = nearest.rename(columns={
        'intersection_id': 'nearest_intersection_id',
        'intersection_type_code': 'nearest_intersection_type_code',
    })
    nearest = nearest[[
        'school_id',
        'school_name',
        'nearest_intersection_id',
        'nearest_intersection_type_code',
        'street_name_1',
        'street_name_2',
        'nearest_intersection_distance_m',
    ]]

    if len(nearest) != len(schools):
        raise RuntimeError('Not every school has one nearest intersection.')
    if nearest['nearest_intersection_id'].isna().any():
        raise RuntimeError('At least one school has no nearest intersection.')
    if (nearest['nearest_intersection_distance_m'] < 0).any():
        raise RuntimeError('Nearest-intersection distances must not be negative.')

    return nearest.sort_values('school_name').reset_index(drop=True)
