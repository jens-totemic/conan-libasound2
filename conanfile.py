import os
from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.client.tools.oss import get_gnu_triplet

class DebianDependencyConan(ConanFile):
    name = "libasound2"
    version = "1.1.0"
    build_version = "0ubuntu1" 
    homepage = "https://packages.ubuntu.com/xenial/libasound2"
    # dev_url = https://packages.ubuntu.com/xenial/libasound2-dev
    description = "shared library for ALSA applications -- development files. This package contains files required for developing software that makes use of libasound2, the ALSA library."
    url = "https://github.com/jens-totemic/conan-libasound2"    
    license = "GNU Lesser General Public License"
    settings = "os", "arch"

    def translate_arch(self):
        arch_string = str(self.settings.arch)
        # ubuntu does not have v7 specific libraries
        if (arch_string) == "armv7hf":
            return "armhf"
        elif (arch_string) == "armv8":
            return "arm64"
        elif (arch_string) == "x86_64":
            return "amd64"
        return arch_string
        
    def _download_extract_deb(self, url, sha256):
        filename = "./download.deb"
        deb_data_file = "data.tar.xz"
        tools.download(url, filename)
        tools.check_sha256(filename, sha256)
        # extract the payload from the debian file
        self.run("ar -x %s %s" % (filename, deb_data_file))
        os.unlink(filename)
        tools.unzip(deb_data_file)
        os.unlink(deb_data_file)

    def triplet_name(self):
        # we only need the autotool class to generate the host variable
        autotools = AutoToolsBuildEnvironment(self)

        # construct path using platform name, e.g. usr/lib/arm-linux-gnueabihf/pkgconfig
        # if not cross-compiling it will be false. In that case, construct the name by hand
        return autotools.host or get_gnu_triplet(str(self.settings.os), str(self.settings.arch), self.settings.get_safe("compiler"))

    def build(self):
        if self.settings.os == "Linux":
            if self.settings.arch == "x86_64":
                # https://packages.ubuntu.com/xenial/amd64/libasound2/download
                sha_lib = "936332b71b4cdb75e9d74e6e08c31fb6e70bfe4fad10f2c78fe33ba1efdd5e36"
                # https://packages.ubuntu.com/xenial/amd64/libasound2-dev/download
                sha_dev = "a219dc3e49a63938ed847c6adf15149851a21caa62848b22905dbd97e264d002"

                url_lib = ("http://us.archive.ubuntu.com/ubuntu/pool/main/a/alsa-lib/libasound2_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://us.archive.ubuntu.com/ubuntu/pool/main/a/alsa-lib/libasound2-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            elif self.settings.arch == "armv8":
                # https://packages.ubuntu.com/xenial/arm64/libasound2/download
                sha_lib = "3bae618a255582a71d89f5d09281f4bf84f26cdf953bd0b09898c3a307e9b441"
                # https://packages.ubuntu.com/xenial/arm64/libasound2-dev/download
                sha_dev = "37385bca2d7bcc52de56dd96e5f1dbf409d2df1e9667f311dbe022a16bdc5117"

                url_lib = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            else: # armv7hf
                # https://packages.ubuntu.com/xenial/armhf/libasound2/download
                sha_lib = "8aa152b840021ab3fbebe2d099a0106f226eec92551c36ce41d5d3310a059849"
                # https://packages.ubuntu.com/xenial/armhf/libasound2-dev/download
                sha_dev = "736d846de5bfcac933c9f35ac47b1e5f128901856ffce08f8865e8dfc8a15966"

                url_lib = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
        else:
            raise Exception("Binary does not exist for these settings")
        self._download_extract_deb(url_lib, sha_lib)
        self._download_extract_deb(url_dev, sha_dev)

    def package(self):
        self.copy(pattern="*", dst="lib", src="usr/lib/" + self.triplet_name(), symlinks=True)
        self.copy(pattern="*", dst="include", src="usr/include", symlinks=True)
        self.copy(pattern="copyright", src="usr/share/doc/" + self.name, symlinks=True)

    def copy_cleaned(self, source, prefix_remove, dest):
        for e in source:
            if (e.startswith(prefix_remove)):
                entry = e[len(prefix_remove):]
                if len(entry) > 0 and not entry in dest:
                    dest.append(entry)

    def package_info(self):
        #pkgpath = "usr/lib/%s/pkgconfig" % self.triplet_name()
        pkgpath =  "lib/pkgconfig"
        pkgconfigpath = os.path.join(self.package_folder, pkgpath)
        self.output.info("package info file: " + pkgconfigpath)
        with tools.environment_append({'PKG_CONFIG_PATH': pkgconfigpath}):
            pkg_config = tools.PkgConfig("alsa", variables={ "prefix" : self.package_folder } )

            self.copy_cleaned(pkg_config.libs_only_L, "-L", self.cpp_info.lib_paths)
            self.output.info("lib_paths %s" % self.cpp_info.lib_paths)

            # exclude all libraries from dependencies here, they are separately included
            self.copy_cleaned(pkg_config.libs_only_l, "-l", self.cpp_info.libs)
            self.output.info("libs: %s" % self.cpp_info.libs)

            self.copy_cleaned(pkg_config.cflags_only_I, "-I", self.cpp_info.include_paths)
            self.output.info("include_paths: %s" % self.cpp_info.include_paths)
