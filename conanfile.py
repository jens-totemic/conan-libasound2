import os
import stat
import glob
import shutil
from conans import ConanFile, AutoToolsBuildEnvironment, tools, errors
from conans.tools import check_md5, check_sha256, check_sha1


class DebianDependencyConan(ConanFile):
    name = "libasound2-dev"
    version = "1.1.0"
    sha     = "8aa152b840021ab3fbebe2d099a0106f226eec92551c36ce41d5d3310a059849"
    sha_dev = "736d846de5bfcac933c9f35ac47b1e5f128901856ffce08f8865e8dfc8a15966"
    homepage = "http://www.alsa-project.org/"
    description = "shared library for ALSA applications -- development files This package contains files required for developing software that makes use of libasound2, the ALSA library."
    url = "https://github.com/jens-totemic/conan-pjsip"    
    settings = "os", "arch"

#     def requirements(self):
#         if self.settings.os == "Linux":
#             self.requires("libalsa/1.1.5@conan/stable")
#         if self.options.SSL:
#             self.requires(_openSSL+"/1.0.2@conan/stable")      

    def translate_arch(self):
        arch_string = str(self.settings.arch)
        # ubuntu does not have v7 specific libraries
        if (arch_string) == "armv7hf":
            return "armhf"
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
            url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2-dev_%s-0ubuntu1_%s.deb"
                   % (str(self.version), self.translate_arch()))
            url = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2_%s-0ubuntu1_%s.deb"
                   % (str(self.version), self.translate_arch()))
        else:
            raise Exception("Binary does not exist for these settings")
        self._download_extract_deb(url, self.sha)
        self._download_extract_deb(url_dev, self.sha_dev)

    def package(self):
        self.copy("*", symlinks=True)

    def copy_cleaned(self, source, prefix_remove, dest, prefix_add, suffix_to_duplicate, excludes):
        for e in source:
            if (e.startswith(prefix_remove)):
                entry = e[len(prefix_remove):]
                full_entry = prefix_add+entry
                if len(entry) > 0 and not full_entry in dest and not full_entry in excludes:
                    dest.append(full_entry)
                    if (suffix_to_duplicate and full_entry.endswith(suffix_to_duplicate)):
                        dest.append(full_entry[:-len(suffix_to_duplicate)])

    def package_info(self):
        self.output.info("package_info")
        # we only need the autotool class to generate the host variable
        autotools = AutoToolsBuildEnvironment(self)
        # construct path using platform name, e.g. usr/lib/arm-linux-gnueabihf/pkgconfig
        pkgpath = "usr/lib/%s/pkgconfig" % autotools.host 
        pkgconfigpath = os.path.join(self.package_folder, pkgpath)
        self.output.info(pkgconfigpath)
        with tools.environment_append({'PKG_CONFIG_PATH': pkgconfigpath}):
            pkg_config = tools.PkgConfig("alsa")
            self.output.info(pkg_config.libs)
            self.output.info(pkg_config.libs_only_L)
            self.output.info(pkg_config.libs_only_l)
            self.output.info(pkg_config.libs_only_other)
            self.output.info(pkg_config.cflags)
            self.output.info(pkg_config.cflags_only_I)
            self.output.info(pkg_config.variables)
        # The entries in the package file are not including the absolute path, add it here
        self.copy_cleaned(pkg_config.libs_only_L, "-L", self.cpp_info.lib_paths, self.package_folder, None, [])
        self.output.info(self.cpp_info.lib_paths)
        
        # exclude all libraries from dependencies here, they are separately included
        self.copy_cleaned(pkg_config.libs_only_l, "-l", self.cpp_info.libs, "", None, [])
        self.output.info(self.cpp_info.libs)

        # when creating include paths, we need to add an additional include directory that does not end on /alsa,
        # so #include<alsa/version.h> works
        self.copy_cleaned(pkg_config.cflags_only_I, "-I", self.cpp_info.include_paths, self.package_folder, "/alsa", [])
        self.output.info(self.cpp_info.include_paths)
