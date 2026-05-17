#!/usr/bin/env python3
#
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
#

import argparse
import os
import shutil

import yaml
from jinja2 import Environment, FileSystemLoader

from loongnix_api import get_supported_versions, get_release_info


def archHelper(arch, os_name):
    # rpm-based distros report loongarch64; dpkg-based report loong64
    if arch == "loong64" and os_name == "anolis":
        return "loongarch64"
    return arch


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Dockerfiles for loong64 JDK images"
    )
    parser.add_argument("--force", action="store_true", help="Force remove old Dockerfiles")
    args = parser.parse_args()

    env = Environment(
        loader=FileSystemLoader("docker_templates"), trim_blocks=False, lstrip_blocks=False
    )

    if args.force:
        for d in os.listdir():
            if d.isdigit():
                print(f"Removing {d}")
                shutil.rmtree(d)

    with open("config/temurin.yml", "r") as f:
        config = yaml.safe_load(f)

    supported_versions = get_supported_versions()

    for os_family, configurations in config["configurations"].items():
        for configuration in configurations:
            directory = configuration["directory"]
            architectures = configuration["architectures"]
            os_name = configuration["os"]
            base_image = configuration["image"]
            deprecated = configuration.get("deprecated", None)
            versions = configuration.get("versions", supported_versions)

            template_name = f"{os_name}.Dockerfile.j2"
            template = env.get_template(template_name)

            for version in versions:
                if deprecated and version >= deprecated:
                    continue

                print(f"Generating Dockerfiles for {base_image} - {version}")

                release = get_release_info(version)
                if release is None:
                    print(f"  No loong64 release found for JDK {version}, skipping")
                    continue

                openjdk_version = release["version_string"]
                if openjdk_version is None:
                    print(f"  Could not parse version string for JDK {version}, skipping")
                    continue

                # Build arch_data using OS-specific arch names
                arch_data = {}
                for arch in architectures:
                    if arch not in release:
                        continue
                    mapped = archHelper(arch, os_name)
                    arch_data[mapped] = {
                        "download_url": release[arch]["download_url"],
                        "checksum": release[arch]["checksum"],
                    }

                if not arch_data:
                    print(f"  No arch data for JDK {version}, skipping")
                    continue

                arch_data = dict(sorted(arch_data.items()))

                # Only JDK images — Loongnix does not ship separate JRE archives
                image_type = "jdk"
                output_directory = os.path.join(str(version), image_type, directory)
                os.makedirs(output_directory, exist_ok=True)

                rendered_dockerfile = template.render(
                    base_image=base_image,
                    image_type=image_type,
                    java_version=openjdk_version,
                    version=version,
                    arch_data=arch_data,
                    os_family=os_family,
                    os=os_name,
                )

                print(f"  Writing Dockerfile to {output_directory}")
                with open(os.path.join(output_directory, "Dockerfile"), "w") as out_file:
                    out_file.write(rendered_dockerfile)

                template_entrypoint = env.get_template("entrypoint.sh.j2")
                entrypoint = template_entrypoint.render(
                    image_type=image_type,
                    os=os_name,
                    version=version,
                )
                with open(os.path.join(output_directory, "entrypoint.sh"), "w") as out_file:
                    out_file.write(entrypoint)

    print("Dockerfiles generated successfully!")
