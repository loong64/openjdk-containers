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

import unittest

from jinja2 import Environment, FileSystemLoader


class TestJinjaRendering(unittest.TestCase):
    def setUp(self):
        self.env = Environment(loader=FileSystemLoader("docker_templates"))

    def _arch_data(self, arch="loong64"):
        return {arch: {"download_url": "https://fake-url.com/jdk.tar.gz", "checksum": "abc123"}}

    # --- debian template ---

    def test_debian_jdk11_contains_download_url(self):
        template = self.env.get_template("debian.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jdk",
            java_version="jdk-11.0.30+7",
            version=11,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertIn("https://fake-url.com/jdk.tar.gz", rendered)
        self.assertIn("abc123", rendered)
        self.assertIn("ghcr.io/loong64/debian:trixie", rendered)

    def test_debian_jdk11_ldconfig_and_xshare(self):
        template = self.env.get_template("debian.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jdk",
            java_version="jdk-11.0.30+7",
            version=11,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertIn("ldconfig", rendered)
        self.assertIn("java -Xshare:dump", rendered)

    def test_debian_jdk8_no_xshare(self):
        template = self.env.get_template("debian.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jdk",
            java_version="jdk8u482-b08",
            version=8,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertNotIn("java -Xshare:dump", rendered)
        self.assertIn("ldconfig", rendered)

    def test_debian_binutils_jdk13(self):
        template = self.env.get_template("debian.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jdk",
            java_version="jdk-13+33",
            version=13,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertIn("binutils", rendered)

    def test_debian_no_binutils_jdk12(self):
        template = self.env.get_template("debian.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jdk",
            java_version="jdk-12+33",
            version=12,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertNotIn("binutils", rendered)

    # --- anolis template ---

    def test_anolis_jdk11_contains_download_url(self):
        template = self.env.get_template("anolis.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/anolis:23",
            image_type="jdk",
            java_version="jdk-11.0.30+7",
            version=11,
            arch_data=self._arch_data("loongarch64"),
            os="anolis",
        )
        self.assertIn("https://fake-url.com/jdk.tar.gz", rendered)
        self.assertIn("abc123", rendered)
        self.assertIn("ghcr.io/loong64/anolis:23", rendered)

    def test_anolis_uses_dnf(self):
        template = self.env.get_template("anolis.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/anolis:23",
            image_type="jdk",
            java_version="jdk-11.0.30+7",
            version=11,
            arch_data=self._arch_data("loongarch64"),
            os="anolis",
        )
        self.assertIn("dnf install", rendered)
        self.assertIn("dnf clean all", rendered)

    # --- arch-variable partial ---

    def test_arch_variable_debian(self):
        template = self.env.get_template("partials/arch-variable.j2")
        rendered = template.render(os="debian")
        self.assertIn("dpkg --print-architecture", rendered)

    def test_arch_variable_anolis(self):
        template = self.env.get_template("partials/arch-variable.j2")
        rendered = template.render(os="anolis")
        self.assertIn("rpm --query", rendered)

    # --- multi-arch-install partial (no GPG) ---

    def test_multi_arch_install_no_gpg(self):
        template = self.env.get_template("partials/multi-arch-install.j2")
        rendered = template.render(
            arch_data=self._arch_data(),
            os="debian",
            image_type="jdk",
            version=11,
        )
        self.assertNotIn("gpg", rendered)
        self.assertIn("md5sum", rendered)
        self.assertIn("wget", rendered)

    # --- version-check partial ---

    def test_version_checker_jdk11(self):
        template = self.env.get_template("partials/version-check.j2")
        rendered = template.render(version="11", image_type="jdk")
        self.assertIn("javac --version", rendered)
        self.assertIn("java --version", rendered)

    def test_version_checker_jdk8(self):
        template = self.env.get_template("partials/version-check.j2")
        rendered = template.render(version="8", image_type="jdk")
        self.assertIn("javac -version", rendered)
        self.assertIn("java -version", rendered)

    def test_version_checker_jre_no_javac(self):
        template = self.env.get_template("partials/version-check.j2")
        rendered = template.render(version="11", image_type="jre")
        self.assertNotIn("javac", rendered)
        self.assertIn("java --version", rendered)

    # --- jshell partial ---

    def test_jshell_jdk11(self):
        template = self.env.get_template("partials/jshell.j2")
        rendered = template.render(version="11", image_type="jdk")
        self.assertIn('CMD ["jshell"]', rendered)

    def test_jshell_jre_no_cmd(self):
        template = self.env.get_template("partials/jshell.j2")
        rendered = template.render(version="17", image_type="jre")
        self.assertNotIn('CMD ["jshell"]', rendered)

    def test_jshell_jdk8_no_cmd(self):
        template = self.env.get_template("partials/jshell.j2")
        rendered = template.render(version="8", image_type="jdk")
        self.assertNotIn('CMD ["jshell"]', rendered)

    # --- entrypoint ---

    def test_entrypoint_debian_uses_bash(self):
        template = self.env.get_template("entrypoint.sh.j2")
        rendered = template.render(image_type="jdk", os="debian", version=11)
        self.assertIn("#!/usr/bin/env bash", rendered)
        self.assertIn("update-ca-certificates", rendered)

    def test_entrypoint_anolis_uses_sh(self):
        template = self.env.get_template("entrypoint.sh.j2")
        rendered = template.render(image_type="jdk", os="anolis", version=11)
        self.assertIn("#!/usr/bin/env sh", rendered)
        self.assertIn("update-ca-trust", rendered)

    # --- debian JRE template ---

    def test_debian_jre11_uses_jlink(self):
        template = self.env.get_template("debian-jre.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jre",
            java_version="jdk-11.0.30+7",
            version=11,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertIn("jlink", rendered)
        self.assertIn("ALL-MODULE-PATH", rendered)
        self.assertIn("COPY --from=jdk-stage /jre", rendered)
        self.assertNotIn("javac", rendered)

    def test_debian_jre8_copies_jre_dir(self):
        template = self.env.get_template("debian-jre.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jre",
            java_version="jdk8u482-b08",
            version=8,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertNotIn("jlink", rendered)
        self.assertIn("COPY --from=jdk-stage $JAVA_HOME/jre", rendered)

    def test_debian_jre_is_multistage(self):
        template = self.env.get_template("debian-jre.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/debian:trixie",
            image_type="jre",
            java_version="jdk-21.0.9+10",
            version=21,
            arch_data=self._arch_data(),
            os="debian",
        )
        self.assertIn("AS jdk-stage", rendered)
        self.assertIn("FROM ghcr.io/loong64/debian:trixie\n", rendered)

    # --- anolis JRE template ---

    def test_anolis_jre11_uses_jlink(self):
        template = self.env.get_template("anolis-jre.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/anolis:23",
            image_type="jre",
            java_version="jdk-11.0.30+7",
            version=11,
            arch_data=self._arch_data("loongarch64"),
            os="anolis",
        )
        self.assertIn("jlink", rendered)
        self.assertIn("COPY --from=jdk-stage /jre", rendered)
        self.assertNotIn("javac", rendered)

    def test_anolis_jre8_copies_jre_dir(self):
        template = self.env.get_template("anolis-jre.Dockerfile.j2")
        rendered = template.render(
            base_image="ghcr.io/loong64/anolis:23",
            image_type="jre",
            java_version="jdk8u482-b08",
            version=8,
            arch_data=self._arch_data("loongarch64"),
            os="anolis",
        )
        self.assertNotIn("jlink", rendered)
        self.assertIn("COPY --from=jdk-stage $JAVA_HOME/jre", rendered)


if __name__ == "__main__":
    unittest.main()
