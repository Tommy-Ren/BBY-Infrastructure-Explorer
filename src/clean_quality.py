"""
Create data-quality summaries for cleaned spatial layers.
"""

import json
import pandas as pd

from clean_config import EARLIEST_SIGNAL_DATE, OUTPUT_CRS, SCHOOL_PLACE_TYPE


def summarize_dataset(source, processed, id_column):
    """
    Summarize record counts, geometry quality, IDs, and missing values.
    """
    missing_values = {
        column: int(processed[column].isna().sum())
        for column in processed.columns
        if column != 'geometry'
    }
    valid_source_geometry = source.geometry.notna()
    return {
        'source_records': len(source),
        'processed_records': len(processed),
        'source_geometry_issues': {
            'missing': int(source.geometry.isna().sum()),
            'empty': int(source.geometry.is_empty.sum()),
            'invalid': int((~source.geometry.is_valid & valid_source_geometry).sum()),
        },
        'processed_missing_ids': int(processed[id_column].isna().sum()),
        'processed_duplicate_ids': int(processed[id_column].duplicated().sum()),
        'processed_missing_values': missing_values,
        'output_crs': processed.crs.to_string(),
    }


def write_data_quality_summary(output_file, places, schools, comparison_places, raw_traffic_calming,
        traffic_calming, raw_traffic_signals, traffic_signals, raw_intersections, intersections):
    """
    Write summary of data quality and cleaning decisions
    """
    school_places = places[places['PLACETYPE'] == SCHOOL_PLACE_TYPE]
    other_places = places[places['PLACETYPE'] != SCHOOL_PLACE_TYPE]
    summary = {
        'output_crs': OUTPUT_CRS,
        'cleaning_decisions': [
            'Schools were selected where PLACETYPE equals 500.',
            'All non-school Places of Interest were kept as the comparison group.',
            'Traffic-signal dates before 1900 were treated as placeholders.',
        ],
        'datasets': {
            'schools': summarize_dataset(school_places, schools, 'school_id'),
            'comparison_places': summarize_dataset(
                other_places, comparison_places, 'place_id'
            ),
            'traffic_calming': summarize_dataset(
                raw_traffic_calming, traffic_calming, 'calming_id'
            ),
            'traffic_signals': summarize_dataset(
                raw_traffic_signals, traffic_signals, 'signal_id'
            ),
            'intersections': summarize_dataset(
                raw_intersections, intersections, 'intersection_id'
            ),
        },
    }
    summary['datasets']['schools']['source_layer_records'] = len(places)
    summary['datasets']['traffic_calming']['undocumented_type_records'] = int(
        traffic_calming['calming_type'].str.startswith('Unlabelled code').sum()
    )
    raw_signal_dates = pd.to_datetime(raw_traffic_signals['INSTDATE'], unit='ms', utc=True, errors='coerce')
    summary['datasets']['traffic_signals']['placeholder_dates_replaced'] = int((raw_signal_dates < EARLIEST_SIGNAL_DATE).sum())

    with output_file.open('w', encoding='utf-8') as output_stream:
        json.dump(summary, output_stream, indent=2)
        output_stream.write('\n')
