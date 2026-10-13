"""
Calculate traffic-calming coverage and category summaries.
"""

import pandas as pd

from analyse_config import COVERAGE_DISTANCES_M


def count_nearby_traffic_calming(schools, traffic_calming):
    """
    Count traffic-calming features within each coverage distance.
    """
    coverage = schools[['school_id', 'school_name']].copy()
    count_columns = []
    for distance_m in COVERAGE_DISTANCES_M:
        column = f'calming_count_{distance_m}m'
        count_columns.append(column)
        coverage[column] = schools.geometry.apply(
            lambda school: int(
                (traffic_calming.geometry.distance(school) <= distance_m).sum()
            )
        )

    if coverage[count_columns].isna().any().any():
        raise RuntimeError('Traffic-calming coverage counts contain missing values.')
    if (coverage[count_columns] < 0).any().any():
        raise RuntimeError('Traffic-calming coverage counts must not be negative.')
    for smaller, larger in zip(count_columns, count_columns[1:]):
        if (coverage[smaller] > coverage[larger]).any():
            raise RuntimeError('Coverage counts must increase with distance.')

    return coverage.sort_values('school_name').reset_index(drop=True)


def summarize_traffic_calming_coverage(coverage):
    """
    Summarize the proportion of schools covered at each distance.
    """
    total_schools = len(coverage)
    if total_schools == 0:
        raise RuntimeError('Empty school coverage table.')

    summary_rows = []
    for distance_m in COVERAGE_DISTANCES_M:
        count_column = f'calming_count_{distance_m}m'
        schools_with_feature = int((coverage[count_column] > 0).sum())
        summary_rows.append({
            'distance_m': distance_m,
            'total_schools': total_schools,
            'schools_with_feature': schools_with_feature,
            'schools_without_feature': total_schools - schools_with_feature,
            'coverage_percent': round(
                100 * schools_with_feature / total_schools, 1
            ),
        })

    return pd.DataFrame(summary_rows)


def summarize_group_traffic_calming_coverage(
        school_coverage, comparison_coverage):
    """
    Summarize school and comparison-place coverage at each distance.
    """
    if school_coverage.empty or comparison_coverage.empty:
        raise RuntimeError('Group coverage inputs must not be empty.')

    summary_rows = []
    for distance_m in COVERAGE_DISTANCES_M:
        school_column = f'calming_count_{distance_m}m'
        comparison_column = f'covered_{distance_m}m'
        if school_column not in school_coverage.columns:
            raise RuntimeError(f'Missing school coverage column: {school_column}')
        if comparison_column not in comparison_coverage.columns:
            raise RuntimeError(
                f'Missing comparison coverage column: {comparison_column}'
            )
        if (
            school_coverage[school_column].isna().any()
            or comparison_coverage[comparison_column].isna().any()
        ):
            raise RuntimeError('Group coverage values contain missing data.')

        school_total = len(school_coverage)
        comparison_total = len(comparison_coverage)
        school_with_feature = int(
            (school_coverage[school_column] > 0).sum()
        )
        comparison_with_feature = int(
            comparison_coverage[comparison_column].sum()
        )
        summary_rows.append({
            'distance_m': distance_m,
            'school_total': school_total,
            'school_with_feature': school_with_feature,
            'school_without_feature': school_total - school_with_feature,
            'school_coverage_percent': round(
                100 * school_with_feature / school_total, 1
            ),
            'comparison_total': comparison_total,
            'comparison_with_feature': comparison_with_feature,
            'comparison_without_feature': (
                comparison_total - comparison_with_feature
            ),
            'comparison_coverage_percent': round(
                100 * comparison_with_feature / comparison_total, 1
            ),
        })

    return pd.DataFrame(summary_rows)


def summarize_traffic_calming_types(schools, traffic_calming, coverage):
    """
    Summarize traffic-calming types found near schools.
    """
    school_feature_pairs = []
    maximum_distance = max(COVERAGE_DISTANCES_M)
    for school in schools.itertuples():
        distances = traffic_calming.geometry.distance(school.geometry)
        nearby = traffic_calming.loc[
            distances <= maximum_distance,
            ['calming_id', 'calming_type'],
        ].copy()
        nearby['school_id'] = school.school_id
        nearby['distance_m'] = distances.loc[nearby.index].to_numpy()
        school_feature_pairs.append(nearby)

    pairs = pd.concat(school_feature_pairs, ignore_index=True)
    pairs['calming_type'] = pairs['calming_type'].fillna('Missing')
    summaries = []
    for distance_m in COVERAGE_DISTANCES_M:
        nearby = pairs[pairs['distance_m'] <= distance_m]
        type_summary = nearby.groupby('calming_type').agg(
            school_feature_pairs=('calming_id', 'size'),
            unique_features=('calming_id', 'nunique'),
            schools_with_type=('school_id', 'nunique'),
        ).reset_index()
        type_summary.insert(0, 'distance_m', distance_m)

        count_column = f'calming_count_{distance_m}m'
        if type_summary['school_feature_pairs'].sum() != coverage[count_column].sum():
            raise RuntimeError('Type totals do not match school coverage counts.')
        summaries.append(type_summary)

    summary = pd.concat(summaries, ignore_index=True)
    summary = summary.sort_values(
        ['distance_m', 'school_feature_pairs', 'calming_type'],
        ascending=[True, False, True],
    )
    return summary.reset_index(drop=True)
