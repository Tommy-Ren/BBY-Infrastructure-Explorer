"""
ArcGIS layer pagination and validation.
"""

from download_config import OUTPUT_SPATIAL_REFERENCE
from download_io import (
    file_sha256,
    get_object_id_field,
    request_json,
    write_json,
)


def download_layer(session, name, layer_url, output_directory):
    """
    Download one complete ArcGIS layer and return its manifest information.
    """
    metadata = request_json(session, layer_url, {'f': 'pjson'})
    object_id_field = get_object_id_field(metadata)

    count_response = request_json(session, layer_url + '/query', {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json',
    })
    expected_count = count_response.get('count')
    if not isinstance(expected_count, int) or expected_count < 0:
        raise RuntimeError(f'Invalid feature count for {name}: {expected_count!r}')

    page_size = metadata.get('maxRecordCount', 1000)
    if not isinstance(page_size, int):
        page_size = 1000
    page_size = max(1, min(page_size, 2000))

    features = []
    first_page_metadata = {}
    while len(features) < expected_count:
        page = request_json(session, layer_url + '/query', {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'outSR': OUTPUT_SPATIAL_REFERENCE,
            'orderByFields': object_id_field + ' ASC',
            'resultOffset': len(features),
            'resultRecordCount': page_size,
            'f': 'geojson',
        })

        page_features = page.get('features')
        if not isinstance(page_features, list):
            raise RuntimeError(f'GeoJSON response for {name} has no feature list')
        if not page_features:
            raise RuntimeError(
                f'{name} returned an empty page after {len(features)} of '
                f'{expected_count} expected records'
            )

        if not first_page_metadata:
            first_page_metadata = {
                key: value for key, value in page.items()
                if key not in ['features', 'exceededTransferLimit']
            }
        features.extend(page_features)

    if len(features) != expected_count:
        raise RuntimeError(
            f'Count mismatch for {name}: downloaded {len(features)}, '
            f'API reported {expected_count}'
        )

    object_ids = [feature['properties'].get(object_id_field) for feature in features]
    missing_object_ids = sum(object_id is None for object_id in object_ids)
    duplicate_object_ids = len(object_ids) - len(set(object_ids))
    if missing_object_ids or duplicate_object_ids:
        raise RuntimeError(
            f'Invalid object IDs for {name}: {missing_object_ids} missing and '
            f'{duplicate_object_ids} duplicated'
        )

    # Recheck membership after pagination; additions/deletions during acquisition
    # must not silently produce a mixed or incomplete layer.
    final_ids = request_json(session, layer_url + '/query', {
        'where': '1=1', 'returnIdsOnly': 'true', 'f': 'json',
    }).get('objectIds')
    if not isinstance(final_ids, list) or set(final_ids) != set(object_ids):
        raise RuntimeError(f'{name} changed during download; retry the refresh')

    missing_geometry = sum(feature.get('geometry') is None for feature in features)
    feature_collection = {
        'type': 'FeatureCollection',
        **{
            key: value for key, value in first_page_metadata.items()
            if key != 'type'
        },
        'features': features,
    }

    geojson_path = output_directory / f'{name}.geojson'
    metadata_path = output_directory / f'{name}.metadata.json'
    write_json(geojson_path, feature_collection)
    write_json(metadata_path, metadata)

    native_spatial_reference = metadata.get('extent', {}).get(
        'spatialReference', {}
    ).get('wkid')

    return {
        'name': name,
        'source_url': layer_url,
        'source_count': expected_count,
        'downloaded_count': len(features),
        'missing_geometry_count': missing_geometry,
        'object_id_field': object_id_field,
        'native_spatial_reference': native_spatial_reference,
        'output_spatial_reference': OUTPUT_SPATIAL_REFERENCE,
        'page_size': page_size,
        'geojson_file': geojson_path.name,
        'geojson_sha256': file_sha256(geojson_path),
        'metadata_file': metadata_path.name,
        'metadata_sha256': file_sha256(metadata_path),
    }
