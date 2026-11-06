"""Read-only Codex metadata diagnostic. Never prints credentials or raw logs."""
import json
import os
import tomllib
from pathlib import Path
from urllib.parse import urlsplit


def main():
    root = Path.home() / '.codex'
    config = tomllib.loads((root / 'config.toml').read_text(encoding='utf-8'))
    providers = config.get('model_providers', {})
    report = {'model': config.get('model'), 'model_provider': config.get('model_provider'),
              'sandbox_mode': config.get('sandbox_mode'), 'providers': []}
    for name, values in providers.items():
        report['providers'].append({'name': name, 'endpoint_host': urlsplit(values.get('base_url', '')).hostname,
                                    'wire_api': values.get('wire_api'),
                                    'credential_env_configured': bool(values.get('env_key')),
                                    'credential_env_present': bool(os.getenv(values.get('env_key', '__NONE__'))),
                                    'requires_openai_auth': values.get('requires_openai_auth')})
    report['matching_log_files'] = []
    log_dir = root / 'log'
    if log_dir.exists():
        for path in log_dir.glob('*.log'):
            with path.open('rb') as stream:
                stream.seek(max(0, path.stat().st_size - 2_000_000))
                sample = stream.read().decode('utf-8', errors='replace')
            count = sample.count('created under a different')
            if count:
                report['matching_log_files'].append({'name': path.name, 'resource_mismatch_errors_in_tail': count})
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
