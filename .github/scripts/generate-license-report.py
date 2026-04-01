#!/usr/bin/env python3
"""
Generate a 3rd-Party Software License Report from SPDX and CycloneDX SBOMs.
Outputs a combined HTML report with component name, version, license info,
and full attribution with license text (Slack-style format).
"""

import json
import argparse
import html
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


# Patterns to identify invalid/local file entries (not real dependencies)
INVALID_PATTERNS = [
    r'^/',                          # Absolute paths
    r'\\',                          # Windows paths
    r'/home/',                      # Home directory paths
    r'/runner/',                    # GitHub runner paths
    r'/work/',                      # GitHub workspace paths
    r'\.github/',                   # GitHub config files
    r'\.yml$',                      # YAML files
    r'\.yaml$',                     # YAML files
    r'\.md$',                       # Markdown files
    r'\.txt$',                      # Text files
    r'\.sh$',                       # Shell scripts
    r'\.gitignore$',                # Git ignore files
    r'\.dockerignore$',             # Docker ignore files
    r'^Dockerfile',                 # Dockerfiles
    r'^Makefile',                   # Makefiles
    r'^LICENSE',                    # License files
    r'^README',                     # README files
    r'^CHANGELOG',                  # Changelog files
]

# Common license texts for standard licenses
STANDARD_LICENSE_TEXTS = {
    'MIT': '''MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.''',

    'Apache-2.0': '''Apache License, Version 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.''',

    'BSD-3-Clause': '''BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.''',

    'BSD-2-Clause': '''BSD 2-Clause "Simplified" License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.''',

    'ISC': '''ISC License

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.''',
}


def is_valid_component(name: str) -> bool:
    """Check if the component name represents a real third-party dependency."""
    if not name or name == 'Unknown':
        return False

    # Check against invalid patterns
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return False

    # Filter out entries that look like file paths (contain path separators)
    if '/' in name and not name.startswith('pkg:'):  # Allow purl format
        # Check if it looks like a package namespace (e.g., @scope/package, org/repo)
        parts = name.split('/')
        if len(parts) > 2:  # More than one slash = likely a file path
            return False
        # Check if any part has a file extension
        for part in parts:
            if re.search(r'\.(yml|yaml|json|md|txt|sh|py|js|ts|go|java|rb|rs)$', part, re.IGNORECASE):
                return False

    return True


def purl_to_registry_url(purl: str) -> str | None:
    """Convert a Package URL (purl) to a registry URL."""
    if not purl or not purl.startswith('pkg:'):
        return None

    # Parse purl format: pkg:type/namespace/name@version
    match = re.match(r'pkg:([^/]+)/(.+?)(?:@(.+))?$', purl)
    if not match:
        return None

    pkg_type = match.group(1)
    name_part = match.group(2)
    version = match.group(3)

    # Handle namespaced packages (e.g., @scope/package)
    name_part = name_part.replace('%40', '@').replace('%2F', '/')

    registry_urls = {
        'npm': f'https://www.npmjs.com/package/{name_part}',
        'pypi': f'https://pypi.org/project/{name_part}/',
        'maven': f'https://mvnrepository.com/artifact/{name_part.replace("/", "/")}',
        'golang': f'https://pkg.go.dev/{name_part}',
        'gem': f'https://rubygems.org/gems/{name_part}',
        'nuget': f'https://www.nuget.org/packages/{name_part}',
        'cargo': f'https://crates.io/crates/{name_part}',
        'composer': f'https://packagist.org/packages/{name_part}',
        'hex': f'https://hex.pm/packages/{name_part}',
        'pub': f'https://pub.dev/packages/{name_part}',
    }

    return registry_urls.get(pkg_type)


def get_license_text(license_id: str, provided_text: str = None) -> str:
    """Get the full license text for a license ID."""
    if provided_text and len(provided_text) > 50:
        return provided_text

    # Check standard licenses
    for key, text in STANDARD_LICENSE_TEXTS.items():
        if key.lower() in license_id.lower():
            return text

    return f"License: {license_id}\n\nFull license text not available. Please refer to the package source for complete license terms."


def parse_spdx(filepath: str) -> tuple[list[dict], int]:
    """Parse SPDX JSON SBOM and extract component license info."""
    components = []
    filtered_count = 0
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        for pkg in data.get('packages', []):
            name = pkg.get('name', 'Unknown')

            if not is_valid_component(name):
                filtered_count += 1
                continue

            version = pkg.get('versionInfo', 'N/A')
            license_info = pkg.get('licenseConcluded') or pkg.get('licenseDeclared') or 'Not Specified'
            if license_info == 'NOASSERTION':
                license_info = 'Not Specified'

            # Try to get purl for registry link
            purl = None
            for ref in pkg.get('externalRefs', []):
                if ref.get('referenceType') == 'purl':
                    purl = ref.get('referenceLocator')
                    break

            components.append({
                'name': name,
                'version': version,
                'license': license_info,
                'purl': purl,
                'license_text': get_license_text(license_info),
            })
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not parse SPDX file {filepath}: {e}")

    return components, filtered_count


def parse_cyclonedx(filepath: str) -> tuple[list[dict], int]:
    """Parse CycloneDX JSON SBOM and extract component license info."""
    components = []
    filtered_count = 0
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        for comp in data.get('components', []):
            name = comp.get('name', 'Unknown')

            if not is_valid_component(name):
                filtered_count += 1
                continue

            version = comp.get('version', 'N/A')
            purl = comp.get('purl')

            # Extract license info and text
            licenses = comp.get('licenses', [])
            license_list = []
            license_text = None

            for lic in licenses:
                if 'license' in lic:
                    lic_data = lic['license']
                    if 'id' in lic_data:
                        license_list.append(lic_data['id'])
                    elif 'name' in lic_data:
                        license_list.append(lic_data['name'])
                    # Try to get embedded license text
                    if 'text' in lic_data and 'content' in lic_data['text']:
                        license_text = lic_data['text']['content']
                elif 'expression' in lic:
                    license_list.append(lic['expression'])

            license_info = ', '.join(license_list) if license_list else 'Not Specified'

            components.append({
                'name': name,
                'version': version,
                'license': license_info,
                'purl': purl,
                'license_text': get_license_text(license_info, license_text),
            })
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not parse CycloneDX file {filepath}: {e}")

    return components, filtered_count


def generate_html(spdx_components: list[dict], cdx_components: list[dict],
                  repo_name: str, output_path: str) -> None:
    """Generate combined HTML report with tabs for SBOM formats and attribution."""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Merge components for attribution tab (deduplicated by name+version)
    seen = set()
    attribution_components = []
    for comp in cdx_components + spdx_components:
        key = f"{comp['name']}@{comp['version']}"
        if key not in seen:
            seen.add(key)
            attribution_components.append(comp)

    attribution_components.sort(key=lambda x: x['name'].lower())

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3rd-Party Software License Report - {html.escape(repo_name)}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        header h1 {{
            font-size: 1.8em;
            margin-bottom: 10px;
        }}
        header p {{
            opacity: 0.9;
            font-size: 0.95em;
        }}
        .tabs {{
            display: flex;
            background: #ecf0f1;
            border-bottom: 2px solid #bdc3c7;
            flex-wrap: wrap;
        }}
        .tab {{
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 0.95em;
            font-weight: 500;
            color: #7f8c8d;
            transition: all 0.3s;
        }}
        .tab:hover {{
            background: #d5dbdb;
        }}
        .tab.active {{
            background: white;
            color: #2c3e50;
            border-bottom: 2px solid white;
            margin-bottom: -2px;
        }}
        .tab-content {{
            display: none;
            padding: 20px;
        }}
        .tab-content.active {{
            display: block;
        }}
        .summary {{
            background: #e8f6ff;
            padding: 15px 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        .summary strong {{
            color: #2980b9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background: #2c3e50;
            color: white;
            font-weight: 500;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .license-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            background: #e8f6ff;
            color: #2980b9;
        }}
        .license-badge.not-specified {{
            background: #fff3cd;
            color: #856404;
        }}
        .search-box {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ecf0f1;
            border-radius: 6px;
            font-size: 1em;
            margin-bottom: 15px;
            transition: border-color 0.3s;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #3498db;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            background: #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .table-wrapper {{
            max-height: 600px;
            overflow-y: auto;
        }}

        /* Attribution tab styles (Slack-style) */
        .attribution-list {{
            max-height: 700px;
            overflow-y: auto;
        }}
        .attribution-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }}
        .attribution-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .attribution-header h3 {{
            margin: 0 0 5px 0;
            font-size: 1.1em;
        }}
        .attribution-header h3 a {{
            color: #2980b9;
            text-decoration: none;
        }}
        .attribution-header h3 a:hover {{
            text-decoration: underline;
        }}
        .attribution-header .version {{
            color: #666;
            font-weight: normal;
            font-size: 0.9em;
        }}
        .attribution-license {{
            padding: 15px 20px;
        }}
        .attribution-license h4 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .license-text {{
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 200px;
            overflow-y: auto;
            display: none;
        }}
        .license-text.expanded {{
            display: block;
        }}
        .show-more-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }}
        .show-more-btn:hover {{
            background: #2980b9;
        }}
        .pkg-link {{
            display: inline-block;
            margin-left: 10px;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>3rd-Party Software License Report</h1>
            <p>Repository: {html.escape(repo_name)} | Generated: {timestamp}</p>
        </header>

        <div class="tabs">
            <button class="tab active" onclick="showTab('attribution')">Full Attribution ({len(attribution_components)})</button>
            <button class="tab" onclick="showTab('spdx')">SPDX ({len(spdx_components)})</button>
            <button class="tab" onclick="showTab('cyclonedx')">CycloneDX ({len(cdx_components)})</button>
        </div>

        <div id="spdx" class="tab-content">
            <div class="summary">
                <strong>SPDX SBOM Summary:</strong> {len(spdx_components)} third-party components detected
            </div>
            <input type="text" class="search-box" placeholder="Search components..." onkeyup="filterTable('spdx-table', this.value)">
            <div class="table-wrapper">
                <table id="spdx-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Component Name</th>
                            <th>Version</th>
                            <th>License</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    # Add SPDX components
    for idx, comp in enumerate(sorted(spdx_components, key=lambda x: x['name'].lower()), 1):
        license_class = 'not-specified' if comp['license'] == 'Not Specified' else ''
        html_content += f'''                        <tr>
                            <td>{idx}</td>
                            <td>{html.escape(comp['name'])}</td>
                            <td>{html.escape(comp['version'])}</td>
                            <td><span class="license-badge {license_class}">{html.escape(comp['license'])}</span></td>
                        </tr>
'''

    html_content += '''                    </tbody>
                </table>
            </div>
        </div>

        <div id="cyclonedx" class="tab-content">
            <div class="summary">
                <strong>CycloneDX SBOM Summary:</strong> ''' + str(len(cdx_components)) + ''' third-party components detected
            </div>
            <input type="text" class="search-box" placeholder="Search components..." onkeyup="filterTable('cdx-table', this.value)">
            <div class="table-wrapper">
                <table id="cdx-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Component Name</th>
                            <th>Version</th>
                            <th>License</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    # Add CycloneDX components
    for idx, comp in enumerate(sorted(cdx_components, key=lambda x: x['name'].lower()), 1):
        license_class = 'not-specified' if comp['license'] == 'Not Specified' else ''
        html_content += f'''                        <tr>
                            <td>{idx}</td>
                            <td>{html.escape(comp['name'])}</td>
                            <td>{html.escape(comp['version'])}</td>
                            <td><span class="license-badge {license_class}">{html.escape(comp['license'])}</span></td>
                        </tr>
'''

    html_content += '''                    </tbody>
                </table>
            </div>
        </div>

        <div id="attribution" class="tab-content active">
            <div class="summary">
                <strong>Full Attribution:</strong> ''' + str(len(attribution_components)) + ''' third-party components with license details
            </div>
            <input type="text" class="search-box" id="attribution-search" placeholder="Search components..." onkeyup="filterAttribution(this.value)">
            <div class="attribution-list">
'''

    # Add Attribution components (Slack-style)
    for idx, comp in enumerate(attribution_components):
        registry_url = purl_to_registry_url(comp.get('purl', ''))
        name_display = comp['name']
        if registry_url:
            name_display = f'<a href="{html.escape(registry_url)}" target="_blank" rel="noopener noreferrer">{html.escape(comp["name"])}</a>'
        else:
            name_display = html.escape(comp['name'])

        license_text_escaped = html.escape(comp.get('license_text', 'License text not available.'))

        html_content += f'''                <div class="attribution-item" data-searchable="{html.escape(comp['name'].lower())} {html.escape(comp['license'].lower())}">
                    <div class="attribution-header">
                        <h3>{name_display} <span class="version">({html.escape(comp['version'])})</span></h3>
                    </div>
                    <div class="attribution-license">
                        <h4>Declared License: {html.escape(comp['license'])}</h4>
                        <button class="show-more-btn" onclick="toggleLicense(this)">Show License Text</button>
                        <div class="license-text">{license_text_escaped}</div>
                    </div>
                </div>
'''

    html_content += '''            </div>
        </div>

        <footer>
            Generated from SBOM files using Syft | License compliance report for third-party dependencies
        </footer>
    </div>

    <script>
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }

        function filterTable(tableId, query) {
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tbody tr');
            const lowerQuery = query.toLowerCase();

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(lowerQuery) ? '' : 'none';
            });
        }

        function filterAttribution(query) {
            const items = document.querySelectorAll('.attribution-item');
            const lowerQuery = query.toLowerCase();

            items.forEach(item => {
                const searchable = item.getAttribute('data-searchable');
                item.style.display = searchable.includes(lowerQuery) ? '' : 'none';
            });
        }

        function toggleLicense(btn) {
            const licenseText = btn.nextElementSibling;
            if (licenseText.classList.contains('expanded')) {
                licenseText.classList.remove('expanded');
                btn.textContent = 'Show License Text';
            } else {
                licenseText.classList.add('expanded');
                btn.textContent = 'Hide License Text';
            }
        }
    </script>
</body>
</html>
'''

    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"License report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate 3rd-Party Software License Report from SBOMs')
    parser.add_argument('--spdx', required=True, help='Path to SPDX JSON SBOM file')
    parser.add_argument('--cyclonedx', required=True, help='Path to CycloneDX JSON SBOM file')
    parser.add_argument('--repo-name', required=True, help='Repository name for report title')
    parser.add_argument('--output', default='license-report.html', help='Output HTML file path')

    args = parser.parse_args()

    print(f"Parsing SPDX SBOM: {args.spdx}")
    spdx_components, spdx_filtered = parse_spdx(args.spdx)
    print(f"  Found {len(spdx_components)} valid components ({spdx_filtered} local files filtered out)")

    print(f"Parsing CycloneDX SBOM: {args.cyclonedx}")
    cdx_components, cdx_filtered = parse_cyclonedx(args.cyclonedx)
    print(f"  Found {len(cdx_components)} valid components ({cdx_filtered} local files filtered out)")

    generate_html(spdx_components, cdx_components, args.repo_name, args.output)


if __name__ == '__main__':
    main()
