"""
Measure transportation-infrastructure coverage around schools.
"""

import pathlib
import sys

from analyse_config import (
    DEFAULT_INPUT_DIRECTORY,
    DEFAULT_OUTPUT_DIRECTORY,
)
from analyse_distances import (
    add_comparison_coverage_flags,
    compare_nearest_calming_distances,
    nearest_comparison_traffic_calming,
    nearest_intersections,
    nearest_traffic_calming,
    nearest_traffic_signals,
)
from analyse_inputs import read_spatial_data
from analyse_proportions import (
    check_coverage_expected_frequencies,
    test_coverage_proportions,
)
from analyse_summaries import (
    count_nearby_traffic_calming,
    summarize_group_traffic_calming_coverage,
    summarize_traffic_calming_coverage,
    summarize_traffic_calming_types,
)
from cluster_features import build_school_feature_table


def main():
    if len(sys.argv) not in [1, 3]:
        print('Usage:')
        print(' python src/analyse_coverage.py [input_directory output_directory]')
        sys.exit(1)

    if len(sys.argv) == 3:
        input_directory = pathlib.Path(sys.argv[1])
        output_directory = pathlib.Path(sys.argv[2])
    else:
        input_directory = DEFAULT_INPUT_DIRECTORY
        output_directory = DEFAULT_OUTPUT_DIRECTORY

    (
        schools,
        comparison_places,
        traffic_calming,
        traffic_signals,
        intersections,
    ) = read_spatial_data(input_directory)

    nearest_calming = nearest_traffic_calming(schools, traffic_calming)
    comparison_nearest_calming = add_comparison_coverage_flags(
        nearest_comparison_traffic_calming(
            comparison_places, traffic_calming
        )
    )
    distance_comparison = compare_nearest_calming_distances(
        nearest_calming, comparison_nearest_calming
    )
    nearest_signals = nearest_traffic_signals(schools, traffic_signals)
    nearest_intersection_results = nearest_intersections(schools, intersections)
    traffic_calming_coverage = count_nearby_traffic_calming(
        schools, traffic_calming
    )
    school_features = build_school_feature_table(
        nearest_calming,
        nearest_signals,
        nearest_intersection_results,
        traffic_calming_coverage,
    )
    coverage_summary = summarize_traffic_calming_coverage(
        traffic_calming_coverage
    )
    group_coverage_summary = summarize_group_traffic_calming_coverage(
        traffic_calming_coverage, comparison_nearest_calming
    )
    coverage_test_assumptions = check_coverage_expected_frequencies(
        group_coverage_summary
    )
    coverage_proportion_tests = test_coverage_proportions(
        group_coverage_summary, coverage_test_assumptions
    )
    type_summary = summarize_traffic_calming_types(
        schools, traffic_calming, traffic_calming_coverage
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    calming_output_file = output_directory / 'school_nearest_traffic_calming.csv'
    comparison_output_file = (
        output_directory / 'comparison_nearest_traffic_calming.csv'
    )
    distance_comparison_file = (
        output_directory / 'traffic_calming_distance_comparison.csv'
    )
    signal_output_file = output_directory / 'school_nearest_traffic_signals.csv'
    intersection_output_file = output_directory / 'school_nearest_intersections.csv'
    coverage_output_file = output_directory / 'school_traffic_calming_coverage.csv'
    school_features_output_file = (
        output_directory / 'school_infrastructure_features.csv'
    )
    summary_output_file = output_directory / 'traffic_calming_coverage_summary.csv'
    group_summary_output_file = (
        output_directory / 'traffic_calming_group_coverage_summary.csv'
    )
    assumptions_output_file = (
        output_directory / 'traffic_calming_coverage_test_assumptions.csv'
    )
    proportion_tests_output_file = (
        output_directory / 'traffic_calming_coverage_proportion_tests.csv'
    )
    type_output_file = output_directory / 'traffic_calming_type_summary.csv'
    nearest_calming.to_csv(
        calming_output_file, index=False, float_format='%.3f'
    )
    comparison_nearest_calming.to_csv(
        comparison_output_file, index=False, float_format='%.3f'
    )
    distance_comparison.to_csv(distance_comparison_file, index=False)
    nearest_signals.to_csv(
        signal_output_file, index=False, float_format='%.3f'
    )
    nearest_intersection_results.to_csv(
        intersection_output_file, index=False, float_format='%.3f'
    )
    traffic_calming_coverage.to_csv(coverage_output_file, index=False)
    school_features.to_csv(
        school_features_output_file,
        index=False,
        float_format='%.3f',
    )
    coverage_summary.to_csv(summary_output_file, index=False)
    group_coverage_summary.to_csv(group_summary_output_file, index=False)
    coverage_test_assumptions.to_csv(assumptions_output_file, index=False)
    coverage_proportion_tests.to_csv(
        proportion_tests_output_file, index=False
    )
    type_summary.to_csv(type_output_file, index=False)

    print(f'Nearest traffic-calming distances for {len(nearest_calming)} schools:')
    print(f'Output: {calming_output_file}')
    print(
        'Nearest traffic-calming distances for '
        f'{len(comparison_nearest_calming)} comparison places:'
    )
    print(f'Output: {comparison_output_file}')
    print('School and comparison-place distance test:')
    print(f'Output: {distance_comparison_file}')
    print(f'Nearest traffic-signal distances for {len(nearest_signals)} schools:')
    print(f'Output: {signal_output_file}')
    print(
        'Nearest-intersection distances for '
        f'{len(nearest_intersection_results)} schools:'
    )
    print(f'Output: {intersection_output_file}')
    print(
        'Traffic-calming coverage counts for '
        f'{len(traffic_calming_coverage)} schools:'
    )
    print(f'Output: {coverage_output_file}')
    print(f'School infrastructure features for {len(school_features)} schools:')
    print(f'Output: {school_features_output_file}')
    print(f'Coverage summary for {len(coverage_summary)} distances:')
    print(f'Output: {summary_output_file}')
    print(f'Group coverage summary for {len(group_coverage_summary)} distances:')
    print(f'Output: {group_summary_output_file}')
    print(
        'Coverage-test assumptions for '
        f'{len(coverage_test_assumptions)} distances:'
    )
    print(f'Output: {assumptions_output_file}')
    print(
        'Coverage-proportion tests for '
        f'{len(coverage_proportion_tests)} distances:'
    )
    print(f'Output: {proportion_tests_output_file}')
    print(f'Traffic-calming type summary with {len(type_summary)} rows:')
    print(f'Output: {type_output_file}')


if __name__ == '__main__':
    main()
