"""
Standardize school infrastructure features and calculate PCA components.
"""

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from cluster_features import SCHOOL_FEATURE_COLUMNS


STANDARDIZED_FEATURE_COLUMNS = [
    f'{column}_z'
    for column in SCHOOL_FEATURE_COLUMNS
]


def standardize_school_features(school_features):
    """
    Standardize numeric features to mean zero and unit variance.
    """
    feature_values = school_features[SCHOOL_FEATURE_COLUMNS]
    if feature_values.isna().any().any():
        raise RuntimeError('School clustering features contain missing values.')

    scaler = StandardScaler()
    standardized_values = scaler.fit_transform(feature_values)
    standardized = pd.DataFrame(
        standardized_values,
        columns=STANDARDIZED_FEATURE_COLUMNS,
    )
    identifiers = school_features[['school_id', 'school_name']].reset_index(
        drop=True
    )
    return pd.concat([identifiers, standardized], axis=1)


def calculate_school_pca(standardized_features):
    """
    Reduce the standardized feature table to two principal components.
    """
    feature_values = standardized_features[STANDARDIZED_FEATURE_COLUMNS]
    if feature_values.isna().any().any():
        raise RuntimeError('Standardized features contain missing values.')

    pca = PCA(n_components=2, svd_solver='full')
    score_values = pca.fit_transform(feature_values)
    scores = standardized_features[['school_id', 'school_name']].copy()
    scores['pc1'] = score_values[:, 0]
    scores['pc2'] = score_values[:, 1]

    explained_variance = pd.DataFrame({
        'component': ['PC1', 'PC2'],
        'explained_variance_ratio': pca.explained_variance_ratio_,
    })
    explained_variance['cumulative_explained_variance_ratio'] = (
        explained_variance['explained_variance_ratio'].cumsum()
    )
    loadings = pd.DataFrame({
        'feature': SCHOOL_FEATURE_COLUMNS,
        'pc1_loading': pca.components_[0],
        'pc2_loading': pca.components_[1],
    })
    return scores, explained_variance, loadings
