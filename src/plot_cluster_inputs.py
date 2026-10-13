"""
Read and validate inputs for the school cluster PCA figure.
"""

import pandas as pd

from plot_config import (
    CLUSTER_ASSIGNMENT_COLUMNS,
    PCA_SCORE_COLUMNS,
    PCA_VARIANCE_COLUMNS,
)


def read_cluster_plot_data(table_directory):
    """
    Read PCA scores, cluster assignments, and explained variance.
    """
    scores_file = table_directory / 'school_pca_scores.csv'
    assignments_file = table_directory / 'school_cluster_assignments.csv'
    variance_file = table_directory / 'school_pca_explained_variance.csv'
    for input_file in [scores_file, assignments_file, variance_file]:
        if not input_file.exists():
            raise RuntimeError(f'Missing input file: {input_file}')

    scores = pd.read_csv(scores_file)
    assignments = pd.read_csv(assignments_file)
    explained_variance = pd.read_csv(variance_file)
    validate_cluster_plot_inputs(scores, assignments, explained_variance)

    cluster_data = scores.merge(
        assignments,
        on=['school_id', 'school_name'],
        how='inner',
        validate='one_to_one',
    )
    if len(cluster_data) != len(scores):
        raise RuntimeError('PCA scores and cluster assignments do not match.')
    return cluster_data, explained_variance


def validate_cluster_plot_inputs(scores, assignments, explained_variance):
    """
    Validate schemas and identifiers used by the cluster figure.
    """
    inputs = [
        ('PCA score', scores, PCA_SCORE_COLUMNS),
        ('Cluster assignment', assignments, CLUSTER_ASSIGNMENT_COLUMNS),
        ('PCA variance', explained_variance, PCA_VARIANCE_COLUMNS),
    ]
    for name, data, required_columns in inputs:
        missing_columns = required_columns - set(data.columns)
        if missing_columns:
            raise RuntimeError(f'Missing {name.lower()} columns: {sorted(missing_columns)}')
        if data.empty:
            raise RuntimeError(f'{name} data must not be empty.')
        if data[list(required_columns)].isna().any().any():
            raise RuntimeError(f'{name} data contains missing values.')

    identifier_inputs = [
        ('PCA score', scores),
        ('Cluster assignment', assignments),
    ]
    for name, data in identifier_inputs:
        if data['school_id'].duplicated().any():
            raise RuntimeError(f'{name} school IDs must be unique.')
    if set(scores['school_id']) != set(assignments['school_id']):
        raise RuntimeError('PCA scores and cluster assignments have different IDs.')
    if set(explained_variance['component']) != {'PC1', 'PC2'}:
        raise RuntimeError('PCA variance must contain PC1 and PC2.')
    if not explained_variance['explained_variance_ratio'].between(0, 1).all():
        raise RuntimeError('PCA explained-variance ratios must be between 0 and 1.')


def build_cluster_map_data(schools, cluster_data):
    """
    Join cluster assignments to the processed school locations.
    """
    if schools['school_id'].duplicated().any():
        raise RuntimeError('School map IDs must be unique.')
    if set(schools['school_id']) != set(cluster_data['school_id']):
        raise RuntimeError('School map and cluster data have different IDs.')

    cluster_map_data = schools.merge(
        cluster_data[['school_id', 'cluster']],
        on='school_id',
        how='inner',
        validate='one_to_one',
    )
    if len(cluster_map_data) != len(schools):
        raise RuntimeError('The cluster map join changed the school count.')
    return cluster_map_data
