"""
Download the raw City of Burnaby ArcGIS layers for the project.
"""

import datetime
import pathlib
import sys

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from download_arcgis import download_layer
from download_config import (
    DEFAULT_OUTPUT_DIRECTORY,
    LAYERS,
    PROJECT_ROOT,
)
from download_io import write_json


def main():
    if len(sys.argv) > 2:
        print('Usage:')
        print(' python src/download_data.py [output_directory]')
        sys.exit(1)

    if len(sys.argv) == 2:
        output_directory = pathlib.Path(sys.argv[1])
    else:
        output_directory = DEFAULT_OUTPUT_DIRECTORY

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET'],
    )))
    session.headers.update({
        'Accept': 'application/json',
        'User-Agent': 'CMPT-353-Project/1.0 (academic data acquisition)',
    })

    layer_results = []
    for name, layer_url in LAYERS.items():
        print(f'Downloading {name}...')
        result = download_layer(session, name, layer_url, output_directory)
        layer_results.append(result)
        print(
            f"  {result['downloaded_count']} records, "
            f"{result['missing_geometry_count']} missing geometries"
        )

    try:
        relative_output = output_directory.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        relative_output = str(output_directory)

    manifest = {
        'schema_version': 1,
        'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source': 'City of Burnaby ArcGIS REST services',
        'output_directory': relative_output,
        'layers': layer_results,
    }
    manifest_path = output_directory / 'manifest.json'
    write_json(manifest_path, manifest)

    total_records = sum(result['downloaded_count'] for result in layer_results)
    print(f'Wrote manifest to {manifest_path}')
    print(f'Validated {total_records} records.')


if __name__ == '__main__':
    main()
