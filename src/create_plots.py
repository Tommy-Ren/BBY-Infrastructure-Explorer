"""
Create figures for the Burnaby school-area coverage analysis.
"""

import pathlib
import sys

from plot_config import (
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_SPATIAL_DIRECTORY,
    DEFAULT_TABLE_DIRECTORY,
    LOW_COVERAGE_SCHOOL_COUNT,
)
from plot_figures import (
    create_coverage_plot,
    create_distance_distribution_plot,
    create_lower_coverage_plot,
    create_overview_map,
)
from plot_inputs import read_coverage_summary, read_distance_data, read_map_data


def main():
    if len(sys.argv) not in [1, 4]:
        print('Usage:')
        print(
            ' python src/create_plots.py '
            '[spatial_directory table_directory output_directory]'
        )
        sys.exit(1)

    if len(sys.argv) == 4:
        spatial_directory = pathlib.Path(sys.argv[1])
        table_directory = pathlib.Path(sys.argv[2])
        output_directory = pathlib.Path(sys.argv[3])
    else:
        spatial_directory = DEFAULT_SPATIAL_DIRECTORY
        table_directory = DEFAULT_TABLE_DIRECTORY
        output_directory = DEFAULT_OUTPUT_DIRECTORY

    schools, traffic_calming, intersections = read_map_data(spatial_directory)
    school_distances, comparison_distances = read_distance_data(table_directory)
    coverage = read_coverage_summary(table_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    map_file = output_directory / 'school_traffic_calming_overview.svg'
    distribution_file = (
        output_directory / 'nearest_traffic_calming_distance_distributions.svg'
    )
    coverage_file = output_directory / 'school_traffic_calming_coverage.svg'
    lower_coverage_file = output_directory / 'lower_coverage_schools.svg'
    create_overview_map(schools, traffic_calming, intersections, map_file)
    create_distance_distribution_plot(
        school_distances, comparison_distances, distribution_file
    )
    create_coverage_plot(coverage, coverage_file)
    create_lower_coverage_plot(school_distances, lower_coverage_file)

    print(f'Created overview map for {len(schools)} schools.')
    print(f'Output: {map_file}')
    print('Created school and comparison-place distance distributions.')
    print(f'Output: {distribution_file}')
    print(f'Created coverage plot for {len(coverage)} distance thresholds.')
    print(f'Output: {coverage_file}')
    print(f'Created lower-coverage ranking for {LOW_COVERAGE_SCHOOL_COUNT} schools.')
    print(f'Output: {lower_coverage_file}')


if __name__ == '__main__':
    main()
