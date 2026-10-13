"""
Check assumptions for school and comparison-place coverage tests.
"""

import pandas as pd
from scipy import stats


MINIMUM_EXPECTED_FREQUENCY = 5
GROUP_COVERAGE_COLUMNS = {
    'distance_m',
    'school_total',
    'school_with_feature',
    'school_without_feature',
    'comparison_total',
    'comparison_with_feature',
    'comparison_without_feature',
}
ASSUMPTION_COLUMNS = {
    'distance_m',
    'all_expected_at_least_5',
}


def holm_adjust_p_values(p_values):
    """
    Adjust a family of p-values with the Holm step-down method.
    """
    if not p_values:
        raise RuntimeError('At least one p-value is required.')
    if any(value < 0 or value > 1 for value in p_values):
        raise RuntimeError('P-values must be between zero and one.')

    adjusted = [0] * len(p_values)
    ordered_indices = sorted(
        range(len(p_values)),
        key=lambda index: p_values[index],
    )
    previous_adjusted = 0
    for rank, index in enumerate(ordered_indices):
        remaining_tests = len(p_values) - rank
        adjusted_value = min(remaining_tests * p_values[index], 1)
        adjusted_value = max(adjusted_value, previous_adjusted)
        adjusted[index] = adjusted_value
        previous_adjusted = adjusted_value
    return adjusted


def check_coverage_expected_frequencies(group_coverage):
    """
    Calculate expected 2-by-2 table frequencies at each distance.
    """
    missing_columns = GROUP_COVERAGE_COLUMNS - set(group_coverage.columns)
    if missing_columns:
        raise RuntimeError(
            'Missing group coverage columns: '
            f'{sorted(missing_columns)}'
        )
    if group_coverage.empty:
        raise RuntimeError('Group coverage summary must not be empty.')
    if group_coverage[list(GROUP_COVERAGE_COLUMNS)].isna().any().any():
        raise RuntimeError('Group coverage summary contains missing values.')

    results = []
    for row in group_coverage.itertuples():
        if (row.school_with_feature + row.school_without_feature != row.school_total):
            raise RuntimeError('School coverage counts do not match the total.')
        if (row.comparison_with_feature + row.comparison_without_feature != row.comparison_total):
            raise RuntimeError('Comparison-place coverage counts do not match the total.')

        total_locations = row.school_total + row.comparison_total
        if total_locations == 0:
            raise RuntimeError('Group coverage totals must be positive.')
        total_with_feature = row.school_with_feature + row.comparison_with_feature
        total_without_feature = row.school_without_feature + row.comparison_without_feature

        expected = {
            'expected_school_with_feature': row.school_total * total_with_feature / total_locations,
            'expected_school_without_feature': row.school_total * total_without_feature / total_locations,
            'expected_comparison_with_feature': row.comparison_total * total_with_feature / total_locations,
            'expected_comparison_without_feature': row.comparison_total * total_without_feature / total_locations
        }
        minimum_expected = min(expected.values())
        results.append({
            'distance_m': row.distance_m,
            **{
                column: round(value, 3)
                for column, value in expected.items()
            },
            'minimum_expected_frequency': round(minimum_expected, 3),
            'all_expected_at_least_5': (
                minimum_expected >= MINIMUM_EXPECTED_FREQUENCY
            ),
        })

    return pd.DataFrame(results)


def test_coverage_proportions(group_coverage, assumptions):
    """
    Select and run a two-sided coverage test at each distance.
    """
    missing_group_columns = GROUP_COVERAGE_COLUMNS - set(group_coverage.columns)
    missing_assumption_columns = ASSUMPTION_COLUMNS - set(assumptions.columns)
    if missing_group_columns:
        raise RuntimeError('Missing group coverage columns: 'f'{sorted(missing_group_columns)}')
    if missing_assumption_columns:
        raise RuntimeError('Missing assumption columns: ' f'{sorted(missing_assumption_columns)}')
    if (group_coverage['distance_m'].duplicated().any() or assumptions['distance_m'].duplicated().any()):
        raise RuntimeError('Coverage-test distances must be unique.')
    if set(group_coverage['distance_m']) != set(assumptions['distance_m']):
        raise RuntimeError('Coverage and assumption distances do not match.')

    assumption_flags = assumptions.set_index(
        'distance_m'
    )['all_expected_at_least_5']
    results = []
    for row in group_coverage.itertuples():
        if row.school_total == 0 or row.comparison_total == 0:
            raise RuntimeError('Coverage group totals must be positive.')
        school_coverage_percent = 100 * row.school_with_feature / row.school_total
        comparison_coverage_percent = 100 * row.comparison_with_feature / row.comparison_total
        school_minus_comparison_pp = school_coverage_percent - comparison_coverage_percent

        contingency_table = [
            [row.school_with_feature, row.school_without_feature],
            [
                row.comparison_with_feature,
                row.comparison_without_feature,
            ],
        ]
        if assumption_flags.loc[row.distance_m]:
            test_result = stats.chi2_contingency(contingency_table)
            test_name = 'Chi-square'
            statistic_name = 'chi_square'
        else:
            test_result = stats.fisher_exact(
                contingency_table,
                alternative='two-sided',
            )
            test_name = "Fisher's exact"
            statistic_name = 'odds_ratio'

        results.append({
            'distance_m': row.distance_m,
            'school_coverage_percent': round(school_coverage_percent, 1),
            'comparison_coverage_percent': round(comparison_coverage_percent, 1),
            'school_minus_comparison_pp': round(school_minus_comparison_pp, 1),
            'test': test_name,
            'alternative': 'two-sided',
            'statistic_name': statistic_name,
            'statistic': test_result.statistic,
            'p_value': test_result.pvalue,
        })

    test_results = pd.DataFrame(results)
    test_results['holm_adjusted_p_value'] = holm_adjust_p_values(
        test_results['p_value'].tolist()
    )
    return test_results
