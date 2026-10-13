"""
Prepare school infrastructure features for profile clustering.
"""

import pathlib
import sys

import pandas as pd

from cluster_diagnostics import (
    calculate_feature_correlations,
    summarize_feature_distributions,
)
from cluster_features import SCHOOL_FEATURE_COLUMNS
from cluster_kmeans import (
    cluster_school_features,
    compare_cluster_counts,
    select_cluster_count,
)
from cluster_pca import calculate_school_pca, standardize_school_features


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_INPUT_FILE = (
    PROJECT_ROOT / 'output' / 'tables' / 'school_infrastructure_features.csv'
)
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / 'output' / 'tables'


def read_school_features(input_file):
    """
    Read and validate the school infrastructure feature table.
    """
    if not input_file.exists():
        raise RuntimeError(f'Missing input file: {input_file}')
    school_features = pd.read_csv(input_file)
    required_columns = {
        'school_id',
        'school_name',
        *SCHOOL_FEATURE_COLUMNS,
    }
    missing_columns = required_columns - set(school_features.columns)
    if missing_columns:
        raise RuntimeError(
            f'Missing school feature columns: {sorted(missing_columns)}'
        )
    if school_features.empty:
        raise RuntimeError('School feature data must not be empty.')
    if (
        school_features['school_id'].isna().any()
        or school_features['school_id'].duplicated().any()
    ):
        raise RuntimeError('School feature IDs are missing or duplicated.')
    if school_features['school_name'].isna().any():
        raise RuntimeError('School feature names are missing.')
    return school_features


def main():
    if len(sys.argv) not in [1, 3]:
        print('Usage:')
        print(
            ' python src/cluster_schools.py '
            '[input_file output_directory]'
        )
        sys.exit(1)

    if len(sys.argv) == 3:
        input_file = pathlib.Path(sys.argv[1])
        output_directory = pathlib.Path(sys.argv[2])
    else:
        input_file = DEFAULT_INPUT_FILE
        output_directory = DEFAULT_OUTPUT_DIRECTORY

    school_features = read_school_features(input_file)
    feature_summary = summarize_feature_distributions(school_features)
    correlations = calculate_feature_correlations(school_features)
    standardized = standardize_school_features(school_features)
    pca_scores, explained_variance, loadings = calculate_school_pca(
        standardized
    )
    cluster_diagnostics = compare_cluster_counts(standardized)
    selected_cluster_count = select_cluster_count(cluster_diagnostics)
    assignments, profiles = cluster_school_features(
        school_features,
        standardized,
        selected_cluster_count,
    )
    cluster_diagnostics['selected'] = (
        cluster_diagnostics['cluster_count'] == selected_cluster_count
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    summary_file = output_directory / 'school_feature_summary.csv'
    correlation_file = output_directory / 'school_feature_correlations.csv'
    standardized_file = output_directory / 'school_features_standardized.csv'
    pca_scores_file = output_directory / 'school_pca_scores.csv'
    pca_variance_file = (
        output_directory / 'school_pca_explained_variance.csv'
    )
    pca_loadings_file = output_directory / 'school_pca_loadings.csv'
    cluster_diagnostics_file = (
        output_directory / 'school_cluster_diagnostics.csv'
    )
    assignments_file = output_directory / 'school_cluster_assignments.csv'
    profiles_file = output_directory / 'school_cluster_profiles.csv'

    feature_summary.to_csv(summary_file, index=False, float_format='%.6f')
    correlations.to_csv(correlation_file, index=False, float_format='%.6f')
    standardized.to_csv(
        standardized_file,
        index=False,
        float_format='%.6f',
    )
    pca_scores.to_csv(pca_scores_file, index=False, float_format='%.6f')
    explained_variance.to_csv(
        pca_variance_file,
        index=False,
        float_format='%.6f',
    )
    loadings.to_csv(pca_loadings_file, index=False, float_format='%.6f')
    cluster_diagnostics.to_csv(
        cluster_diagnostics_file,
        index=False,
        float_format='%.6f',
    )
    assignments.to_csv(assignments_file, index=False)
    profiles.to_csv(profiles_file, index=False, float_format='%.6f')

    print(f'Feature diagnostics for {len(school_features)} schools:')
    print(f'Output: {summary_file}')
    print(f'Output: {correlation_file}')
    print(f'Standardized features: {standardized_file}')
    print(f'PCA scores: {pca_scores_file}')
    print(f'PCA explained variance: {pca_variance_file}')
    print(f'PCA loadings: {pca_loadings_file}')
    print(f'Cluster diagnostics: {cluster_diagnostics_file}')
    print(f'Selected cluster count: {selected_cluster_count}')
    print(f'Cluster assignments: {assignments_file}')
    print(f'Cluster profiles: {profiles_file}')


if __name__ == '__main__':
    main()
