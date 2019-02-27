import os
import stat
import glob
import shutil
from conans import ConanFile, AutoToolsBuildEnvironment, tools, errors
from conans.tools import check_md5, check_sha256, check_sha1
from conans.client.tools.oss import get_gnu_triplet

class DebianDependencyConan(ConanFile):
    name = "libasound2-dev"
    version = "1.1.0"
    buildv =  "0ubuntu1" 
    homepage = "http://www.alsa-project.org/"
    description = "shared library for ALSA applications -- development files. This package contains files required for developing software that makes use of libasound2, the ALSA library."
    url = "https://github.com/jens-totemic/conan-pjsip"    
    settings = "os", "arch"

    def translate_arch(self):
        arch_string = str(self.settings.arch)
        # ubuntu does not have v7 specific libraries
        if (arch_string) == "armv7hf":
            return "armhf"
        elif (arch_string) == "x86_64":
            return "amd64"
        return arch_string
        
    def _download_extract_deb(self, url, sha256):
        filename = "./download.deb"
        deb_data_file = "data.tar.xz"
        tools.download(url, filename)
        tools.check_sha256(filename, sha256)
        # extract the payload from the debian file
        self.run("ar -x %s %s" % (filename, deb_data_file)),
        os.unlink(filename)
        tools.unzip(deb_data_file)
        os.unlink(deb_data_file)

    def build(self):
        if self.settings.os == "Linux":
            if self.settings.arch == "x86_64":
                
                sha     = "936332b71b4cdb75e9d74e6e08c31fb6e70bfe4fad10f2c78fe33ba1efdd5e36"
                sha_dev = "a219dc3e49a63938ed847c6adf15149851a21caa62848b22905dbd97e264d002"
                url_dev = ("http://us.archive.ubuntu.com/ubuntu/pool/main/a/alsa-lib/libasound2-dev_%s-%s_%s.deb"
                   % (str(self.version), self.buildv, self.translate_arch()))
                url = ("http://us.archive.ubuntu.com/ubuntu/pool/main/a/alsa-lib/libasound2_%s-%s_%s.deb"
                   % (str(self.version), self.buildv, self.translate_arch()))
            else:
                sha     = "8aa152b840021ab3fbebe2d099a0106f226eec92551c36ce41d5d3310a059849"
                sha_dev = "736d846de5bfcac933c9f35ac47b1e5f128901856ffce08f8865e8dfc8a15966"
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2-dev_%s-%s_%s.deb"
                   % (str(self.version), self.buildv, self.translate_arch()))
                url = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2_%s-%s_%s.deb"
                   % (str(self.version), self.buildv, self.translate_arch()))
        else:
            raise Exception("Binary does not exist for these settings")
        self._download_extract_deb(url, sha)
        self._download_extract_deb(url_dev, sha_dev)

    def package(self):
        self.copy("*", symlinks=True)

    def copy_cleaned(self, source, prefix_remove, dest):
        for e in source:
            if (e.startswith(prefix_remove)):
                entry = e[len(prefix_remove):]
                if len(entry) > 0 and not entry in dest:
                    dest.append(entry)

    def package_info(self):
        # we only need the autotool class to generate the host variable
        autotools = AutoToolsBuildEnvironment(self)

        # construct path using platform name, e.g. usr/lib/arm-linux-gnueabihf/pkgconfig
        # if not cross-compiling it will be false. In that case, construct the name by hand
        triplet = autotools.host or get_gnu_triplet(str(self.settings.os), str(self.settings.arch), self.settings.get_safe("compiler"))
        pkgpath = "usr/lib/%s/pkgconfig" % triplet
        pkgconfigpath = os.path.join(self.package_folder, pkgpath)
        self.output.info("package info file: " + pkgconfigpath)
        with tools.environment_append({'PKG_CONFIG_PATH': pkgconfigpath}):
            pkg_config = tools.PkgConfig("alsa", variables={ "prefix" : self.package_folder + "/usr" } )

            self.copy_cleaned(pkg_config.libs_only_L, "-L", self.cpp_info.lib_paths)
            self.output.info("lib_paths %s" % self.cpp_info.lib_paths)

            # exclude all libraries from dependencies here, they are separately included
            self.copy_cleaned(pkg_config.libs_only_l, "-l", self.cpp_info.libs)
            self.output.info("libs: %s" % self.cpp_info.libs)

            self.copy_cleaned(pkg_config.cflags_only_I, "-I", self.cpp_info.include_paths)
            self.output.info("include_paths: %s" % self.cpp_info.include_paths)
