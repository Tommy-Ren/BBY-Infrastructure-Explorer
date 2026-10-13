"""
Create the school infrastructure cluster PCA figure.
"""

import matplotlib.pyplot as plt


plt.rcParams['svg.hashsalt'] = 'burnaby-school-clusters'


def create_cluster_pca_plot(cluster_data, explained_variance, output_file):
    """
    Plot K-means assignments in the first two PCA dimensions.
    """
    variance = explained_variance.set_index(
        'component'
    )['explained_variance_ratio']
    colours = ['#0072b2', '#d55e00', '#009e73', '#cc79a7', '#e69f00']
    markers = ['o', '^', 's', 'D', 'P']

    figure, axes = plt.subplots(figsize=(8, 6.5))
    for position, (cluster, schools) in enumerate(
            cluster_data.groupby('cluster')):
        axes.scatter(
            schools['pc1'],
            schools['pc2'],
            color=colours[position % len(colours)],
            marker=markers[position % len(markers)],
            edgecolor='white',
            linewidth=0.5,
            s=58,
            alpha=0.85,
            label=f'Cluster {cluster} (n={len(schools)})',
        )

    axes.axhline(0, color='#999999', linewidth=0.6, zorder=0)
    axes.axvline(0, color='#999999', linewidth=0.6, zorder=0)
    axes.set_title('School Infrastructure Profiles in PCA Space')
    axes.set_xlabel(f'PC1 ({100 * variance.loc["PC1"]:.1f}% variance)')
    axes.set_ylabel(f'PC2 ({100 * variance.loc["PC2"]:.1f}% variance)')
    axes.grid(linewidth=0.5, alpha=0.2)
    axes.legend(title='K-means assignment', frameon=True)

    figure.tight_layout()
    figure.savefig(output_file, dpi=200, metadata={'Date': None})
    plt.close(figure)


def create_cluster_map(cluster_schools, intersections, output_file):
    """
    Map school cluster assignments with intersection context.
    """
    colours = ['#0072b2', '#d55e00', '#009e73', '#cc79a7', '#e69f00']
    markers = ['o', '^', 's', 'D', 'P']

    figure, axes = plt.subplots(figsize=(8, 8))
    intersections.plot(
        ax=axes,
        color='#b8b8b8',
        markersize=2,
        alpha=0.3,
        zorder=1,
    )
    for position, (cluster, schools) in enumerate(
            cluster_schools.groupby('cluster')):
        schools.plot(
            ax=axes,
            color=colours[position % len(colours)],
            marker=markers[position % len(markers)],
            edgecolor='white',
            linewidth=0.5,
            markersize=48,
            label=f'Cluster {cluster} (n={len(schools)})',
            zorder=2,
        )

    map_bounds = intersections.total_bounds
    padding = 300
    axes.set_xlim(map_bounds[0] - padding, map_bounds[2] + padding)
    axes.set_ylim(map_bounds[1] - padding, map_bounds[3] + padding)
    axes.set_title('Burnaby School Infrastructure Profile Clusters')
    axes.set_xlabel('Easting (m, EPSG:26910)')
    axes.set_ylabel('Northing (m, EPSG:26910)')
    axes.ticklabel_format(style='plain', useOffset=False)
    axes.set_aspect('equal')
    axes.legend(title='K-means assignment', loc='lower left', frameon=True)

    figure.tight_layout()
    figure.savefig(output_file, dpi=200, metadata={'Date': None})
    plt.close(figure)
