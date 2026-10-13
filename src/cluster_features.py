"""
Build school-level infrastructure features for profile clustering.
"""


SCHOOL_FEATURE_COLUMNS = [
    'nearest_calming_distance_m',
    'nearest_signal_distance_m',
    'nearest_intersection_distance_m',
    'calming_count_100m',
    'calming_count_250m',
    'calming_count_500m',
]


def validate_school_feature_source(data, source_name, value_columns):
    """
    Validate one school-level result before joining feature columns.
    """
    required_columns = {'school_id', 'school_name', *value_columns}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise RuntimeError(
            f'Missing {source_name} columns: {sorted(missing_columns)}'
        )
    if data.empty:
        raise RuntimeError(f'{source_name} data must not be empty.')
    if data['school_id'].isna().any() or data['school_id'].duplicated().any():
        raise RuntimeError(f'{source_name} school IDs are missing or duplicated.')
    if data['school_name'].isna().any():
        raise RuntimeError(f'{source_name} school names are missing.')


def build_school_feature_table(
        nearest_calming, nearest_signals, nearest_intersections, coverage):
    """
    Join existing school results into one clustering feature table.
    """
    sources = [
        (
            'nearest traffic-calming',
            nearest_calming,
            ['nearest_calming_distance_m'],
        ),
        (
            'nearest traffic-signal',
            nearest_signals,
            ['nearest_signal_distance_m'],
        ),
        (
            'nearest intersection',
            nearest_intersections,
            ['nearest_intersection_distance_m'],
        ),
        (
            'traffic-calming coverage',
            coverage,
            [
                'calming_count_100m',
                'calming_count_250m',
                'calming_count_500m',
            ],
        ),
    ]
    for source_name, data, value_columns in sources:
        validate_school_feature_source(data, source_name, value_columns)

    reference_names = nearest_calming.set_index('school_id')['school_name']
    expected_ids = set(reference_names.index)
    for source_name, data, value_columns in sources[1:]:
        if set(data['school_id']) != expected_ids:
            raise RuntimeError(
                f'{source_name} school IDs do not match the reference data.'
            )
        source_names = data.set_index('school_id')['school_name']
        if not source_names.reindex(reference_names.index).equals(
            reference_names
        ):
            raise RuntimeError(
                f'{source_name} school names do not match the reference data.'
            )

    features = nearest_calming[[
        'school_id',
        'school_name',
        'nearest_calming_distance_m',
    ]].copy()
    for _, data, value_columns in sources[1:]:
        features = features.merge(
            data[['school_id', *value_columns]],
            on='school_id',
            how='inner',
            validate='one_to_one',
        )

    if len(features) != len(nearest_calming):
        raise RuntimeError('The school feature join changed the row count.')
    features = features[[
        'school_id',
        'school_name',
        *SCHOOL_FEATURE_COLUMNS,
    ]]
    return features.sort_values('school_name').reset_index(drop=True)
