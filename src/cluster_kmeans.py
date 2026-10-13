"""
Compare K-means solutions and summarize school infrastructure
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from cluster_features import SCHOOL_FEATURE_COLUMNS
from cluster_pca import STANDARDIZED_FEATURE_COLUMNS


def compare_cluster_counts(standardized_features):
    """
    Compare a small range of cluster counts with silhouette scores.
    """
    feature_values = standardized_features[STANDARDIZED_FEATURE_COLUMNS]
    if feature_values.isna().any().any():
        raise RuntimeError('Standardized features contain missing values.')

    results = []
    for cluster_count in range(2, 6):
        if cluster_count >= len(feature_values):
            raise RuntimeError('The number of schools must exceed cluster count.')
        model = KMeans(n_clusters=cluster_count, random_state=0, n_init=10)
        labels = model.fit_predict(feature_values)
        cluster_sizes = pd.Series(labels).value_counts()
        results.append({
            'cluster_count': cluster_count,
            'inertia': model.inertia_,
            'silhouette_score': silhouette_score(feature_values, labels),
            'smallest_cluster_size': int(cluster_sizes.min()),
            'largest_cluster_size': int(cluster_sizes.max()),
        })
    return pd.DataFrame(results)


def select_cluster_count(cluster_diagnostics):
    """
    Select the cluster count with the greatest silhouette score.
    """
    required_columns = {'cluster_count', 'silhouette_score'}
    missing_columns = required_columns - set(cluster_diagnostics.columns)
    if missing_columns:
        raise RuntimeError(f'Missing cluster diagnostic columns: {sorted(missing_columns)}')
    if cluster_diagnostics.empty:
        raise RuntimeError('Cluster diagnostics must not be empty.')
    if cluster_diagnostics[list(required_columns)].isna().any().any():
        raise RuntimeError('Cluster diagnostics contain missing values.')

    selected_index = cluster_diagnostics['silhouette_score'].idxmax()
    return int(cluster_diagnostics.loc[selected_index, 'cluster_count'])


def cluster_school_features(
        school_features, standardized_features, cluster_count):
    """
    Assign schools to clusters and summarize original-unit medians.
    """
    school_ids = school_features['school_id'].reset_index(drop=True)
    standardized_ids = standardized_features['school_id'].reset_index(drop=True)
    if not school_ids.equals(standardized_ids):
        raise RuntimeError('School and standardized feature rows are not aligned.')

    feature_values = standardized_features[STANDARDIZED_FEATURE_COLUMNS]
    model = KMeans(n_clusters=cluster_count, random_state=0, n_init=10)

    labels = model.fit_predict(feature_values)

    assignments = school_features[['school_id', 'school_name']].copy()
    assignments['cluster'] = labels

    profiled = school_features[['school_id', *SCHOOL_FEATURE_COLUMNS,]].merge(
        assignments[['school_id', 'cluster']],
        on='school_id',
        how='inner',
        validate='one_to_one',
    )

    profiles = profiled.groupby('cluster')[SCHOOL_FEATURE_COLUMNS].median()
    cluster_sizes = profiled.groupby('cluster').size().rename('school_count')
    profiles = cluster_sizes.to_frame().join(profiles).reset_index()
    return assignments, profiles
