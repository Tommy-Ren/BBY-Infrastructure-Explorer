"""
Create the school infrastructure cluster PCA figure.
"""

import pathlib
import sys

from plot_cluster_figures import create_cluster_map, create_cluster_pca_plot
from plot_cluster_inputs import build_cluster_map_data, read_cluster_plot_data
from plot_config import (
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_SPATIAL_DIRECTORY,
    DEFAULT_TABLE_DIRECTORY,
)
from plot_inputs import read_map_data


def main():
    if len(sys.argv) not in [1, 4]:
        print('Usage:')
        print(
            ' python src/create_cluster_plot.py '
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

    cluster_data, explained_variance = read_cluster_plot_data(table_directory)
    schools, _, intersections = read_map_data(spatial_directory)
    cluster_schools = build_cluster_map_data(schools, cluster_data)
    output_directory.mkdir(parents=True, exist_ok=True)
    pca_file = output_directory / 'school_infrastructure_clusters_pca.svg'
    map_file = output_directory / 'school_infrastructure_clusters_map.svg'
    create_cluster_pca_plot(cluster_data, explained_variance, pca_file)
    create_cluster_map(cluster_schools, intersections, map_file)

    print(f'Created PCA cluster plot for {len(cluster_data)} schools.')
    print(f'Output: {pca_file}')
    print(f'Created cluster map for {len(cluster_schools)} schools.')
    print(f'Output: {map_file}')


if __name__ == '__main__':
    main()
