"""
Clean the Burnaby spatial datasets used in the analysis.
"""

import pathlib
import sys

from clean_config import (
    DEFAULT_INPUT_DIRECTORY,
    DEFAULT_OUTPUT_DIRECTORY,
)
from clean_layers import (
    clean_comparison_places,
    clean_intersections,
    clean_schools,
    clean_traffic_calming,
    clean_traffic_signals,
)
from clean_quality import write_data_quality_summary
from clean_readers import (
    read_intersections,
    read_place_type_labels,
    read_places,
    read_traffic_calming,
    read_traffic_signals,
)


def main():
    if len(sys.argv) not in [1, 3]:
        print('Usage:')
        print(' python src/clean_data.py [input_directory output_directory]')
        sys.exit(1)

    if len(sys.argv) == 3:
        input_directory = pathlib.Path(sys.argv[1])
        output_directory = pathlib.Path(sys.argv[2])
    else:
        input_directory = DEFAULT_INPUT_DIRECTORY
        output_directory = DEFAULT_OUTPUT_DIRECTORY

    places = read_places(input_directory)
    place_type_labels = read_place_type_labels(input_directory)
    schools = clean_schools(places)
    comparison_places = clean_comparison_places(places, place_type_labels)
    raw_traffic_calming, type_labels = read_traffic_calming(input_directory)
    traffic_calming = clean_traffic_calming(raw_traffic_calming, type_labels)
    raw_traffic_signals = read_traffic_signals(input_directory)
    traffic_signals = clean_traffic_signals(raw_traffic_signals)
    raw_intersections = read_intersections(input_directory)
    intersections = clean_intersections(raw_intersections)

    output_directory.mkdir(parents=True, exist_ok=True)
    schools_file = output_directory / 'schools.geojson'
    comparison_places_file = output_directory / 'comparison_places.geojson'
    traffic_calming_file = output_directory / 'traffic_calming.geojson'
    traffic_signals_file = output_directory / 'traffic_signals.geojson'
    intersections_file = output_directory / 'intersections.geojson'
    summary_file = output_directory / 'data_quality_summary.json'
    schools.to_file(schools_file, driver='GeoJSON')
    comparison_places.to_file(comparison_places_file, driver='GeoJSON')
    traffic_calming.to_file(traffic_calming_file, driver='GeoJSON')
    traffic_signals.to_file(traffic_signals_file, driver='GeoJSON')
    intersections.to_file(intersections_file, driver='GeoJSON')
    write_data_quality_summary(
        summary_file, places, schools, comparison_places, raw_traffic_calming,
        traffic_calming, raw_traffic_signals, traffic_signals,
        raw_intersections, intersections
    )

    print(f'{len(places)} places of interest.')
    print(f'{len(schools)} schools in {schools.crs}.')
    # print(f'Output: {schools_file}')
    print(f'{len(comparison_places)} comparison places in {comparison_places.crs}.')
    print(f'{len(traffic_calming)} traffic-calming features.')
    print(f'traffic-calming features in {traffic_calming.crs}.')
    # print(f'Output: {traffic_calming_file}')
    print(f'{len(traffic_signals)} traffic signals in {traffic_signals.crs}.')
    # print(f'Output: {traffic_signals_file}')
    print(f'{len(intersections)} intersections in {intersections.crs}.')
    # print(f'Output: {intersections_file}')
    #print(f'Data-quality summary: {summary_file}')


if __name__ == '__main__':
    main()
