"""
Summarize school clustering features before modelling
"""

import pandas as pd

from cluster_features import SCHOOL_FEATURE_COLUMNS


def summarize_feature_distributions(school_features):
    """
    Report missing values and descriptive statistics for each feature.
    """
    total_schools = len(school_features)
    if total_schools == 0:
        raise RuntimeError('School feature data must not be empty.')

    summaries = []
    for column in SCHOOL_FEATURE_COLUMNS:
        values = school_features[column]
        summaries.append({
            'feature': column,
            'total_schools': total_schools,
            'non_missing': int(values.notna().sum()),
            'missing_count': int(values.isna().sum()),
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'q1': values.quantile(0.25),
            'median': values.median(),
            'q3': values.quantile(0.75),
            'max': values.max(),
        })
    return pd.DataFrame(summaries)


def calculate_feature_correlations(school_features):
    """
    Calculate Pearson correlations between numeric clustering features.
    """
    correlations = school_features[SCHOOL_FEATURE_COLUMNS].corr(
        method='pearson'
    )
    correlations.index.name = 'feature'
    return correlations.reset_index()
