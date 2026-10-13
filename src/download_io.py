"""
HTTP and file helpers for the ArcGIS download pipeline.
"""

import hashlib
import json
import requests

from download_config import REQUEST_TIMEOUT


def request_json(session, url, params):
    """
    Request JSON from the API and report HTTP or ArcGIS errors clearly.
    """
    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise RuntimeError(f'Request failed for {url}: {error}') from error
    except ValueError as error:
        raise RuntimeError(f'Response from {url} was not valid JSON') from error

    if not isinstance(data, dict):
        raise RuntimeError(f'Expected a JSON object from {url}')
    if 'error' in data:
        raise RuntimeError(f"ArcGIS error from {url}: {data['error']}")
    return data


def get_object_id_field(metadata):
    """
    Find the object-ID field in the ArcGIS metadata.
    """
    for field in metadata.get('fields', []):
        if field.get('type') == 'esriFieldTypeOID':
            return field['name']
    raise RuntimeError('Layer metadata does not define an object-ID field')


def write_json(path, data):
    """
    Write through a temporary file so an interrupted run cannot corrupt data.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + '.tmp')
    try:
        with temporary_path.open('w', encoding='utf-8', newline='\n') as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.write('\n')
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
