"""
Create figures for the school-area coverage analysis
"""

import matplotlib.pyplot as plt

from plot_config import LOW_COVERAGE_SCHOOL_COUNT


plt.rcParams['svg.hashsalt'] = 'burnaby-school-coverage'


def create_overview_map(schools, traffic_calming, intersections, output_file):
    """
    Plot schools and traffic-calming features with intersection context.
    """
    figure, axes = plt.subplots(figsize=(8, 8))
    intersections.plot(
        ax=axes,
        color='#b8b8b8',
        markersize=2,
        alpha=0.35,
        label='Intersections (context)',
        zorder=1,
    )
    traffic_calming.plot(
        ax=axes,
        color='#e69f00',
        markersize=8,
        alpha=0.55,
        label='Traffic-calming features',
        zorder=2,
    )
    schools.plot(
        ax=axes,
        color='#0072b2',
        edgecolor='white',
        linewidth=0.4,
        marker='^',
        markersize=38,
        label='Schools',
        zorder=3,
    )

    map_bounds = intersections.total_bounds
    padding = 300
    axes.set_xlim(map_bounds[0] - padding, map_bounds[2] + padding)
    axes.set_ylim(map_bounds[1] - padding, map_bounds[3] + padding)
    axes.set_title('Burnaby Schools and Traffic-Calming Features')
    axes.set_xlabel('Easting (m, EPSG:26910)')
    axes.set_ylabel('Northing (m, EPSG:26910)')
    axes.ticklabel_format(style='plain', useOffset=False)
    axes.set_aspect('equal')
    axes.legend(loc='lower left', frameon=True)

    figure.tight_layout()
    figure.savefig(output_file, dpi=200, metadata={'Date': None})
    plt.close(figure)


def create_distance_distribution_plot(
        school_distances, comparison_distances, output_file):
    """
    Plot both nearest-distance distributions with shared scales and bins.
    """
    distance_column = 'nearest_calming_distance_m'
    maximum_distance = max(
        school_distances[distance_column].max(),
        comparison_distances[distance_column].max(),
    )
    bin_width = 50
    upper_distance = int(maximum_distance // bin_width + 1) * bin_width
    bins = list(range(0, upper_distance + bin_width, bin_width))
    groups = [
        ('Schools', school_distances[distance_column], '#0072b2'),
        (
            'Comparison places',
            comparison_distances[distance_column],
            '#d55e00',
        ),
    ]

    figure, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(8, 6),
        sharex=True,
        sharey=True,
    )
    for axes_item, (label, distances, colour) in zip(axes, groups):
        weights = [100 / len(distances)] * len(distances)
        axes_item.hist(
            distances,
            bins=bins,
            weights=weights,
            color=colour,
            alpha=0.8,
            edgecolor='white',
        )
        median_distance = distances.median()
        axes_item.axvline(
            median_distance,
            color=colour,
            linewidth=2,
            linestyle='--',
        )
        axes_item.set_title(label, loc='left')
        axes_item.text(
            0.98,
            0.84,
            f'n = {len(distances)}; median = {median_distance:.1f} m',
            horizontalalignment='right',
            transform=axes_item.transAxes,
        )
        axes_item.set_ylabel('Locations per bin (%)')
        axes_item.grid(axis='y', linewidth=0.5, alpha=0.25)

    axes[-1].set_xlabel('Distance to nearest traffic-calming feature (m)')
    figure.suptitle('Nearest Traffic-Calming Distance Distributions')
    figure.tight_layout()
    figure.savefig(output_file, dpi=200, metadata={'Date': None})
    plt.close(figure)


def create_coverage_plot(coverage, output_file):
    """
    Plot the percentage of schools covered at each distance threshold.
    """
    labels = coverage['distance_m'].astype(str) + ' m'
    figure, axes = plt.subplots(figsize=(7, 5))
    bars = axes.bar(
        labels,
        coverage['coverage_percent'],
        color='#0072b2',
        width=0.65,
    )
    bar_labels = [
        f'{row.coverage_percent:.1f}%\n'
        f'({row.schools_with_feature}/{row.total_schools})'
        for row in coverage.itertuples()
    ]
    axes.bar_label(bars, labels=bar_labels, padding=4)
    axes.set_ylim(0, 110)
    axes.set_yticks(range(0, 101, 20))
    axes.set_title('Schools Near Traffic-Calming Features')
    axes.set_xlabel('Distance threshold')
    axes.set_ylabel('Schools with at least one feature (%)')
    axes.grid(axis='y', linewidth=0.5, alpha=0.25)

    figure.tight_layout()
    figure.savefig(output_file, dpi=200, metadata={'Date': None})
    plt.close(figure)


def create_lower_coverage_plot(school_distances, output_file):
    """
    Rank the schools with the greatest nearest-feature distances.
    """
    distance_column = 'nearest_calming_distance_m'
    school_count = min(LOW_COVERAGE_SCHOOL_COUNT, len(school_distances))
    ranked = school_distances.nlargest(
        school_count, distance_column
    ).sort_values(distance_column)
    ranked = ranked.copy()
    ranked['school_name'] = ranked['school_name'].str.strip()

    figure, axes = plt.subplots(figsize=(9, 6.5))
    bars = axes.barh(
        ranked['school_name'],
        ranked[distance_column],
        color='#0072b2',
        height=0.7,
    )
    bar_labels = [
        f'{distance:.1f} m'
        for distance in ranked[distance_column]
    ]
    axes.bar_label(bars, labels=bar_labels, padding=4)
    axes.set_xlim(0, ranked[distance_column].max() * 1.17)
    axes.set_title('Schools Farthest from Traffic-Calming Features')
    axes.set_xlabel('Distance to nearest traffic-calming feature (m)')
    axes.grid(axis='x', linewidth=0.5, alpha=0.25)

    figure.tight_layout()
    figure.savefig(output_file, dpi=200, metadata={'Date': None})
    plt.close(figure)
