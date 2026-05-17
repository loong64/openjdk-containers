# openjdk-loongson

Docker images for OpenJDK on **loong64 (LoongArch64)**, built from [Loongnix FTP](https://ftp.loongnix.cn/Java/) binaries and published to `ghcr.io/loong64/openjdk-loongson`.

## Supported Images

| Version | Type | Distro | Image tag |
|---------|------|--------|-----------|
| 8, 11, 17, 21, … | `jdk` | Debian Trixie | `ghcr.io/loong64/openjdk-loongson:<ver>-jdk-trixie` |
| 8, 11, 17, 21, … | `jre` | Debian Trixie | `ghcr.io/loong64/openjdk-loongson:<ver>-jre-trixie` |
| 8, 11, 17, 21, … | `jdk` | Anolis 23 | `ghcr.io/loong64/openjdk-loongson:<ver>-jdk-anolis-23` |
| 8, 11, 17, 21, … | `jre` | Anolis 23 | `ghcr.io/loong64/openjdk-loongson:<ver>-jre-anolis-23` |

Each version also has a full-version tag, e.g. `21.0.9_10-jdk-trixie`.

JRE images (JDK 11+) are built with `jlink --add-modules ALL-MODULE-PATH` from the corresponding JDK stage. JDK 8 JRE images copy the bundled `jre/` directory from the JDK tarball.

All images target `linux/loong64` only.

## Usage

```bash
# Pull and run JDK 21 on Debian Trixie
docker run --rm --platform linux/loong64 \
  ghcr.io/loong64/openjdk-loongson:21-jdk-trixie java --version

# Pull and run JRE 21 on Anolis 23
docker run --rm --platform linux/loong64 \
  ghcr.io/loong64/openjdk-loongson:21-jre-anolis-23 java --version
```

## Maintenance

### Automated Dockerfile updates

A [scheduled workflow](.github/workflows/updater.yml) runs every 30 minutes. It calls [`generate_dockerfiles.py`](./generate_dockerfiles.py), which scrapes the [Loongnix FTP](https://ftp.loongnix.cn/Java/) for the latest `glibc2.34` binaries and regenerates all Dockerfiles from the Jinja2 templates in [`docker_templates/`](./docker_templates/). Any changes are submitted as a pull request.

To trigger it manually, go to [Actions → Dockerfile Updater](../../actions/workflows/updater.yml) and click **Run workflow**.

### Building and releasing images

Images are built and pushed to `ghcr.io/loong64/openjdk-loongson` via the [Release workflow](.github/workflows/release.yml).

Go to [Actions → Release](../../actions/workflows/release.yml), click **Run workflow**, and fill in:

| Input | Description | Default |
|-------|-------------|---------|
| `versions` | Comma-separated JDK major versions, or `all` | `all` |
| `image_types` | `jdk`, `jre`, or `jdk,jre` | `jdk,jre` |
| `push` | Whether to push to `ghcr.io` | `true` |

### Dockerfile structure

```
<version>/<jdk|jre>/<distro>/<os_version>/Dockerfile
```

Examples:
- `21/jdk/debian/trixie/Dockerfile`
- `21/jre/anolis/23/Dockerfile`

Templates live in [`docker_templates/`](./docker_templates/):

| Template | Used for |
|----------|----------|
| `debian.Dockerfile.j2` | Debian JDK |
| `debian-jre.Dockerfile.j2` | Debian JRE (multi-stage, jlink) |
| `anolis.Dockerfile.j2` | Anolis JDK |
| `anolis-jre.Dockerfile.j2` | Anolis JRE (multi-stage, jlink) |

### Generating the manifest file

To regenerate the Stackbrew-format manifest (used for registry metadata):

```bash
python3 dockerhub_doc_config_update.py
```

This writes a file named `containers` in the current directory.

### Running tests locally

```bash
pip install -r requirements.txt
python3 -m unittest test_generate_dockerfiles test_dockerhub_doc_config_update -v
```
