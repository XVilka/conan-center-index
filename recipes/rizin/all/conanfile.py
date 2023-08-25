import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import (
    apply_conandata_patches, copy, export_conandata_patches, get,
    rename, replace_in_file, rm, rmdir
)
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"


class RizinConan(ConanFile):
    name = "rizin"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://rizin.re"
    description = "Rizin is a UNIX-like reverse engineering framework and command-line toolset."
    topics = ("rizin")
    license = ("LGPL-3-only",)
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
        "with_swift_demangler": [True, False],
        "debugger": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_zlib": True,
        "with_swift_demangler": True,
        "debugger": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("capstone/5.0", transitive_headers=True)
        self.requires("openssl/3.1.2", transitive_headers=True)
        self.requires("libzip/1.9.2", transitive_headers=True)
        self.requires("lz4/1.9.4", transitive_headers=True)
        self.requires("xxhash/0.8.2", transitive_headers=True)
        self.requires("xz_utils/5.4.2", transitive_headers=True)
        if self.options.with_zlib:
            self.requires("zlib/1.2.13", transitive_headers=True)

    def build_requirements(self):
        self.tool_requires("meson/1.1.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = MesonToolchain(self)
        tc.project_options["debugger"] = ("true" if self.options.debugger
                                         else "false")
        tc.project_options["use_zlib"] = ("true" if self.options.with_zlib
                                     else "false")
        tc.project_options["use_swift_demangler"] = ("true" if self.options.with_swift_demangler
                                     else "false")
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "meson.build"), "subdir('test')", "")

    def build(self):
        self._patch_sources()
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "COPYING.LESSER", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        lib_folder = os.path.join(self.package_folder, "lib")
        rmdir(self, os.path.join(lib_folder, "pkgconfig"))
        rm(self, "*.la", lib_folder)
        fix_apple_shared_install_name(self)
        if is_msvc(self):
            prefix = "rizin"
            rename(self, os.path.join(lib_folder, f"{prefix}.a"), os.path.join(lib_folder, f"{prefix}.lib"))

    def package_info(self):
        self.cpp_info.libs = ['librizin'] if self.settings.os == "Windows" else ['rizin']
        self.cpp_info.includedirs.append(os.path.join("include", "rizin"))
        self.cpp_info.set_property("pkg_config_name", "rz_core")
        self.cpp_info.set_property("component_version", str(Version(self.version).major))
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["pthread", "m"]
