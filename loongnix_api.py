# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import urllib.request
from html.parser import HTMLParser

LOONGNIX_FTP_BASE = "https://ftp.loongnix.cn/Java/openjdk{version}/"

# All known JDK major versions available on Loongnix FTP
CANDIDATE_VERSIONS = [8, 11, 17, 21, 22, 23, 24, 25, 26]

# Standard Java LTS versions
LTS_VERSIONS = {8, 11, 17, 21, 25}

class LoongnixNetworkError(RuntimeError):
    """Raised when network access to Loongnix FTP fails."""

class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value and not value.startswith("#") and value != "..":
                    self.links.append(value)


def _fetch_directory_listing(version):
    url = LOONGNIX_FTP_BASE.format(version=version)
    req = urllib.request.Request(url, headers={"User-Agent": "Loongnix Dockerfile Updater"})
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        raise LoongnixNetworkError(
            f"Failed to fetch directory listing from {url}: {e}"
        ) from e

    parser = _LinkParser()
    parser.feed(html)
    return parser.links


def _loongson_version_key(filename):
    """Return a sortable tuple from a filename like loongson11.17.26-fx-..."""
    match = re.match(r"loongson(\d+)\.(\d+)\.(\d+)", filename)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return (0, 0, 0)


def _parse_jdk_version_string(filename, version):
    """Extract a canonical JDK version string from a Loongnix filename.

    Examples:
      loongson8.1.26-fx-jdk8u482b08-...  -> jdk8u482-b08
      loongson11.17.26-fx-jdk11.0.30_7-... -> jdk-11.0.30+7
      loongson23.1.17-fx-jdk23_37-...    -> jdk-23+37
    """
    if version == 8:
        m = re.search(r"jdk(8u\d+)b(\d+)", filename)
        if m:
            return f"jdk{m.group(1)}-b{m.group(2)}"
    else:
        # e.g. jdk11.0.30_7
        m = re.search(r"jdk(\d+\.\d+\.\d+)_(\d+)", filename)
        if m:
            return f"jdk-{m.group(1)}+{m.group(2)}"
        # e.g. jdk23_37
        m = re.search(r"jdk(\d+)_(\d+)", filename)
        if m:
            return f"jdk-{m.group(1)}+{m.group(2)}"
    return None


def _fetch_md5(url):
    """Fetch the MD5 hex digest from a .md5sum file (format: '<hash>  <filename>')."""
    req = urllib.request.Request(url, headers={"User-Agent": "Loongnix Dockerfile Updater"})
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8").strip()
    except Exception as e:
        raise LoongnixNetworkError(
            f"Failed to fetch checksum from {url}: {e}"
        ) from e
    return content.split()[0]


def get_supported_versions():
    """Return JDK major versions that have loong64 (glibc2.34) binaries on Loongnix FTP."""
    supported = []
    for version in CANDIDATE_VERSIONS:
        links = _fetch_directory_listing(version)
        if any("glibc2.34" in link and link.endswith(".tar.gz") for link in links):
            supported.append(version)
    return supported


def get_latest_lts():
    """Return the highest LTS version that has loong64 binaries on Loongnix FTP."""
    supported = get_supported_versions()
    lts_supported = [v for v in supported if v in LTS_VERSIONS]
    return max(lts_supported) if lts_supported else 21


def get_release_info(version):
    """Return release info for the latest loong64 JDK build of the given major version.

    Returns a dict:
      {
        "loong64": {"download_url": str, "checksum": str},
        "version_string": str,   # e.g. "jdk-11.0.30+7"
      }
    or None if no loong64 build is available.
    """
    links = _fetch_directory_listing(version)
    glibc_files = [l for l in links if "glibc2.34" in l and l.endswith(".tar.gz")]

    if not glibc_files:
        return None

    glibc_files.sort(key=_loongson_version_key)
    latest_file = glibc_files[-1]

    base_url = LOONGNIX_FTP_BASE.format(version=version)
    download_url = base_url + latest_file
    checksum = _fetch_md5(download_url + ".md5sum")
    version_string = _parse_jdk_version_string(latest_file, version)

    return {
        "loong64": {
            "download_url": download_url,
            "checksum": checksum,
        },
        "version_string": version_string,
    }
