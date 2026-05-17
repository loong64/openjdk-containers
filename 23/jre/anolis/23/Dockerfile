# ------------------------------------------------------------------------------
#             NOTE: THIS FILE IS GENERATED VIA "generate_dockerfiles.py"
#
#                       PLEASE DO NOT EDIT IT DIRECTLY.
# ------------------------------------------------------------------------------
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

FROM ghcr.io/loong64/anolis:23 AS jdk-stage

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

# Default to UTF-8 file.encoding
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'

RUN set -eux; \
    dnf install -y \
        gzip \
        tar \
        binutils \
        wget \
        ca-certificates \
        openssl \
    ; \
    dnf clean all

ENV JAVA_VERSION=jdk-23+37


RUN set -eux; \
    ARCH="$(rpm --query --queryformat='%{ARCH}' rpm)"; \
    case "${ARCH}" in \
       loongarch64) \
         ESUM='4dc208fa3afd92cb1f2ed23c57ec1ada'; \
         BINARY_URL='https://ftp.loongnix.cn/Java/openjdk23/loongson23.1.17-fx-jdk23_37-linux-loongarch64-glibc2.34.tar.gz'; \
         ;; \
       *) \
         echo "Unsupported arch: ${ARCH}"; \
         exit 1; \
         ;; \
    esac; \
    wget --progress=dot:giga -O /tmp/openjdk.tar.gz ${BINARY_URL}; \
    echo "${ESUM}  /tmp/openjdk.tar.gz" | md5sum -c -; \
    mkdir -p "$JAVA_HOME"; \
    tar --extract \
        --file /tmp/openjdk.tar.gz \
        --directory "$JAVA_HOME" \
        --strip-components 1 \
        --no-same-owner \
    ; \
    rm -f /tmp/openjdk.tar.gz ${JAVA_HOME}/lib/src.zip;

RUN jlink \
        --add-modules ALL-MODULE-PATH \
        --strip-debug \
        --no-man-pages \
        --no-header-files \
        --compress=2 \
        --output /jre



FROM ghcr.io/loong64/anolis:23

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

# Default to UTF-8 file.encoding
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'

RUN set -eux; \
    dnf install -y \
        tzdata \
        ca-certificates \
        openssl \
        fontconfig \
        glibc-langpack-en \
    ; \
    dnf clean all

ENV JAVA_VERSION=jdk-23+37


COPY --from=jdk-stage /jre $JAVA_HOME


RUN set -eux; \
    echo "Verifying install ..."; \
    echo "java --version"; java --version; \
    echo "Complete."
COPY --chmod=755 entrypoint.sh /__cacert_entrypoint.sh
ENTRYPOINT ["/__cacert_entrypoint.sh"]