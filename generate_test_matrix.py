#!/usr/bin/env python3
# Generates the GitHub Actions build matrix for test-pr.yml.
# Replaces the bashbrew-based approach since loong64 is not in bashbrew's arch list.

import json
import os

import yaml


def main():
    with open("config/temurin.yml") as f:
        config = yaml.safe_load(f)

    includes = []

    for ver_str in sorted(
        (d for d in os.listdir(".") if d.isdigit()), key=int
    ):
        for pkg in ["jdk", "jre"]:
            for cfg in config["configurations"].get("linux", []):
                directory = cfg["directory"]
                base_image = cfg["image"]
                dfdir = os.path.join(ver_str, pkg, directory)
                dockerfile = os.path.join(dfdir, "Dockerfile")
                if not os.path.exists(dockerfile):
                    continue

                slug = directory.replace("/", "-")
                tag = f"loong64-test:{ver_str}-{pkg}-{slug}"
                name = f"{ver_str}-{pkg}-{slug}"

                ver = int(ver_str)
                version_flag = "-version" if ver == 8 else "--version"

                includes.append({
                    "name": name,
                    "os": "ubuntu-latest",
                    "runs": {
                        "prepare": "\n".join([
                            "{ echo FROM busybox:latest; echo RUN :; }"
                            " | docker build --no-cache --tag image-list-marker -",
                        ]),
                        "pull": f"docker pull {base_image} || true",
                        "build": (
                            f"docker buildx build --progress plain"
                            f" --platform linux/loong64"
                            f" --load"
                            f" --tag {tag}"
                            f" {dfdir}"
                        ),
                        "test": (
                            f"docker run --rm --platform linux/loong64"
                            f" {tag} java {version_flag}"
                        ),
                        "images": "docker image ls --filter since=image-list-marker",
                    },
                })

    strategy = {
        "fail-fast": False,
        "matrix": {"include": includes},
    }
    print(json.dumps(strategy))


if __name__ == "__main__":
    main()
