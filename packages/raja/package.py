# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import socket
import glob
import re

from spack.package import *


def spec_uses_toolchain(spec):
    gcc_toolchain_regex = re.compile(".*gcc-toolchain.*")
    using_toolchain = list(filter(gcc_toolchain_regex.match, spec.compiler_flags["cxxflags"]))
    return using_toolchain

def spec_uses_gccname(spec):
    gcc_name_regex = re.compile(".*gcc-name.*")
    using_gcc_name = list(filter(gcc_name_regex.match, spec.compiler_flags["cxxflags"]))
    return using_gcc_name

def hip_repair_cache(options, spec):
    # there is only one dir like this, but the version component is unknown
    options.append(
        cmake_cache_path(
            "HIP_CLANG_INCLUDE_PATH",
            glob.glob("{}/lib/clang/*/include".format(spec["llvm-amdgpu"].prefix))[0],
        )
    )

def hip_for_radiuss_projects(options, spec, spec_compiler):
    # Here is what is typically needed for radiuss projects when building with rocm
    hip_root = spec["hip"].prefix
    rocm_root = hip_root + "/.."
    options.append(cmake_cache_path("HIP_ROOT_DIR", hip_root))
    options.append(cmake_cache_path("ROCM_ROOT_DIR", rocm_root))

    hip_repair_cache(options, spec)

    archs = spec.variants["amdgpu_target"].value
    if archs != "none":
        arch_str = ",".join(archs)
        options.append(
            cmake_cache_string("HIP_HIPCC_FLAGS", "--amdgpu-target={0}".format(arch_str))
        )
        options.append(
            cmake_cache_string("CMAKE_HIP_ARCHITECTURES", arch_str)
        )

    # adrienbernede-22-11:
    #   Specific to Umpire, attempt port to RAJA and CHAI
    hip_link_flags = ""
    if "%gcc" in spec:
        gcc_bin = os.path.dirname(spec_compiler.cxx)
        gcc_prefix = join_path(gcc_bin, "..")
        options.append(cmake_cache_string("HIP_CLANG_FLAGS", "--gcc-toolchain={0}".format(gcc_prefix)))
        options.append(cmake_cache_string("CMAKE_EXE_LINKER_FLAGS", hip_link_flags + " -Wl,-rpath {}/lib64".format(gcc_prefix)))
    else:
        options.append(cmake_cache_string("CMAKE_EXE_LINKER_FLAGS", "-Wl,-rpath={0}/llvm/lib/".format(rocm_root)))

def cuda_for_radiuss_projects(options, spec):
    # Here is what is typically needed for radiuss projects when building with cuda

    cuda_flags = []
    if not spec.satisfies("cuda_arch=none"):
        cuda_arch = spec.variants["cuda_arch"].value
        cuda_flags.append("-arch sm_{0}".format(cuda_arch[0]))
        options.append(
            cmake_cache_string("CUDA_ARCH", "sm_{0}".format(cuda_arch[0])))
        options.append(
            cmake_cache_string("CMAKE_CUDA_ARCHITECTURES", "{0}".format(cuda_arch[0])))
    if spec_uses_toolchain(spec):
        cuda_flags.append("-Xcompiler {}".format(spec_uses_toolchain(spec)[0]))
    if (spec.satisfies("%gcc@8.1: target=ppc64le")):
        cuda_flags.append("-Xcompiler -mno-float128")
    options.append(cmake_cache_string("CMAKE_CUDA_FLAGS", " ".join(cuda_flags)))

def blt_link_helpers(options, spec, spec_compiler):

    ### From local package:
    fortran_compilers = ["gfortran", "xlf"]
    if any(compiler in spec_compiler.fc for compiler in fortran_compilers) and ("clang" in spec_compiler.cxx):
        # Pass fortran compiler lib as rpath to find missing libstdc++
        libdir = os.path.join(os.path.dirname(
                       os.path.dirname(spec_compiler.fc)), "lib")
        flags = ""
        for _libpath in [libdir, libdir + "64"]:
            if os.path.exists(_libpath):
                flags += " -Wl,-rpath,{0}".format(_libpath)
        description = ("Adds a missing libstdc++ rpath")
        if flags:
            options.append(cmake_cache_string("BLT_EXE_LINKER_FLAGS", flags, description))

        # Ignore conflicting default gcc toolchain
        options.append(cmake_cache_string("BLT_CMAKE_IMPLICIT_LINK_DIRECTORIES_EXCLUDE",
        "/usr/tce/packages/gcc/gcc-4.9.3/lib64;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64/gcc/powerpc64le-unknown-linux-gnu/4.9.3;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64;/usr/tce/packages/gcc/gcc-4.9.3/lib64/gcc/x86_64-unknown-linux-gnu/4.9.3"))

    compilers_using_toolchain = ["pgi", "xl", "icpc"]
    if any(compiler in spec_compiler.cxx for compiler in compilers_using_toolchain):
        if spec_uses_toolchain(spec) or spec_uses_gccname(spec):

            # Ignore conflicting default gcc toolchain
            options.append(cmake_cache_string("BLT_CMAKE_IMPLICIT_LINK_DIRECTORIES_EXCLUDE",
            "/usr/tce/packages/gcc/gcc-4.9.3/lib64;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64/gcc/powerpc64le-unknown-linux-gnu/4.9.3;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64;/usr/tce/packages/gcc/gcc-4.9.3/lib64/gcc/x86_64-unknown-linux-gnu/4.9.3"))



class Raja(CachedCMakePackage, CudaPackage, ROCmPackage):
    """RAJA Parallel Framework."""

    homepage = "https://software.llnl.gov/RAJA/"
    git = "https://github.com/LLNL/RAJA.git"
    tags = ["radiuss", "e4s"]

    maintainers = ["davidbeckingsale"]

    version("develop", branch="develop", submodules=False)
    version("main", branch="main", submodules=False)
    version("2022.10.4", tag="v2022.10.4", submodules=False)
    version("2022.10.3", tag="v2022.10.3", submodules=False)
    version("2022.10.2", tag="v2022.10.2", submodules=False)
    version("2022.10.1", tag="v2022.10.1", submodules=False)
    version("2022.10.0", tag="v2022.10.0", submodules=False)
    version("2022.03.1", tag="v2022.03.1", submodules=False)
    version("2022.03.0", tag="v2022.03.0", submodules=False)
    version("0.14.0", tag="v0.14.0", submodules="True")
    version("0.13.0", tag="v0.13.0", submodules="True")
    version("0.12.1", tag="v0.12.1", submodules="True")
    version("0.12.0", tag="v0.12.0", submodules="True")
    version("0.11.0", tag="v0.11.0", submodules="True")
    version("0.10.1", tag="v0.10.1", submodules="True")
    version("0.10.0", tag="v0.10.0", submodules="True")
    version("0.9.0", tag="v0.9.0", submodules="True")
    version("0.8.0", tag="v0.8.0", submodules="True")
    version("0.7.0", tag="v0.7.0", submodules="True")
    version("0.6.0", tag="v0.6.0", submodules="True")
    version("0.5.3", tag="v0.5.3", submodules="True")
    version("0.5.2", tag="v0.5.2", submodules="True")
    version("0.5.1", tag="v0.5.1", submodules="True")
    version("0.5.0", tag="v0.5.0", submodules="True")
    version("0.4.1", tag="v0.4.1", submodules="True")
    version("0.4.0", tag="v0.4.0", submodules="True")

    # export targets when building pre-2.4.0 release with BLT 0.4.0+
    patch(
        "https://github.com/LLNL/RAJA/commit/eca1124ee4af380d6613adc6012c307d1fd4176b.patch?full_index=1",
        sha256="12bb78c00b6683ad3e7fd4e3f87f9776bae074b722431b79696bc862816735ef",
        when="@:0.13.0 ^blt@0.4:",
    )

    variant("openmp", default=True, description="Build OpenMP backend")
    variant("shared", default=True, description="Build shared libs")
    variant("examples", default=True, description="Build examples.")
    variant("exercises", default=True, description="Build exercises.")
    # TODO: figure out gtest dependency and then set this default True
    # and remove the +tests conflict below.
    variant("tests", default=False, description="Build tests")
    variant("libcpp", default=False, description="Uses libc++ instead of libstdc++")
    variant("desul", default=False, description="Build desul atomics backend")
    variant("vectorization", default=True, description="Build SIMD/SIMT intrinsics support")

    depends_on("blt")
    depends_on("blt@0.5.2:", type="build", when="@2022.10.0:")
    depends_on("blt@0.5.0:", type="build", when="@0.14.1:")
    depends_on("blt@0.4.1", type="build", when="@0.14.0")
    depends_on("blt@0.4.0:", type="build", when="@0.13.0")
    depends_on("blt@0.3.6:", type="build", when="@:0.12.0")

    depends_on("camp@2022.10.1:", type="build", when="@2022.10.3:")
    depends_on("camp@2022.10.0:", type="build", when="@2022.10.0:")
    depends_on("camp@2022.03.0:", type="build", when="@2022.03.0:")
    depends_on("camp@0.2.2:0.2.3", when="@0.14.0")
    depends_on("camp@0.1.0", when="@0.10.0:0.13.0")
    depends_on("camp@2022.10.0:", when="@2022.10.0:")
    depends_on("camp@2022.03.2:", when="@2022.03.0:")
    depends_on("camp@main", when="@main")
    depends_on("camp@main", when="@develop")
    depends_on("camp+openmp", when="+openmp")

    depends_on("cmake@3.20:", when="@2022.10.0:", type="build")
    depends_on("cmake@3.23:", when="@2022.10.0: +rocm", type="build")
    depends_on("cmake@3.14:", when="@2022.03.0:", type="build")
    depends_on("cmake@:3.20", when="@2022.03.0:2022.03 +rocm", type="build")

    depends_on("llvm-openmp", when="+openmp %apple-clang")

    depends_on("rocprim", when="+rocm")
    with when("+rocm @0.12.0:"):
        depends_on("camp+rocm")
        for arch in ROCmPackage.amdgpu_targets:
            depends_on(
                "camp+rocm amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch)
            )
        conflicts("+openmp", when="@:2022.03")

    with when("+cuda @0.12.0:"):
        depends_on("camp+cuda")
        for sm_ in CudaPackage.cuda_arch_values:
            depends_on("camp +cuda cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    def _get_sys_type(self, spec):
        sys_type = spec.architecture
        if "SYS_TYPE" in env:
            sys_type = env["SYS_TYPE"]
        return sys_type

    @property
    # TODO: name cache file conditionally to cuda and libcpp variants
    def cache_name(self):
        hostname = socket.gethostname()
        if "SYS_TYPE" in env:
            hostname = hostname.rstrip("1234567890")
        return "{0}-{1}-{2}@{3}-{4}.cmake".format(
            hostname,
            self._get_sys_type(self.spec),
            self.spec.compiler.name,
            self.spec.compiler.version,
            self.spec.dag_hash(8)
        )

    def initconfig_compiler_entries(self):
        spec = self.spec
        compiler = self.compiler
        # Default entries are already defined in CachedCMakePackage, inherit them:
        entries = super(Raja, self).initconfig_compiler_entries()

        # Switch to hip as a CPP compiler.
        # adrienbernede-22-11:
        #   This was only done in upstream Spack raja package.
        #   I could not find the equivalent logic in Spack source, so keeping it.
        if "+rocm" in spec:
            entries.insert(0, cmake_cache_path("CMAKE_CXX_COMPILER", spec["hip"].hipcc))

        # Override CachedCMakePackage CMAKE_C_FLAGS and CMAKE_CXX_FLAGS add
        # +libcpp specific flags
        flags = spec.compiler_flags

        # use global spack compiler flags
        cppflags = " ".join(flags["cppflags"])
        if cppflags:
            # avoid always ending up with " " with no flags defined
            cppflags += " "

        cflags = cppflags + " ".join(flags["cflags"])
        if "+libcpp" in spec:
            cflags += " ".join([cflags,"-DGTEST_HAS_CXXABI_H_=0"])
        if cflags:
            entries.append(cmake_cache_string("CMAKE_C_FLAGS", cflags))

        cxxflags = cppflags + " ".join(flags["cxxflags"])
        if "+libcpp" in spec:
            cxxflags += " ".join([cxxflags,"-stdlib=libc++ -DGTEST_HAS_CXXABI_H_=0"])
        if cxxflags:
            entries.append(cmake_cache_string("CMAKE_CXX_FLAGS", cxxflags))

        blt_link_helpers(entries, spec, compiler)

        return entries

    def initconfig_hardware_entries(self):
        spec = self.spec
        compiler = self.compiler
        entries = super(Raja, self).initconfig_hardware_entries()

        entries.append(cmake_cache_option("ENABLE_OPENMP", "+openmp" in spec))

        if "+cuda" in spec:
            entries.append(cmake_cache_option("ENABLE_CUDA", True))
            cuda_for_radiuss_projects(entries, spec)
        else:
            entries.append(cmake_cache_option("ENABLE_CUDA", False))

        if "+rocm" in spec:
            entries.append(cmake_cache_option("ENABLE_HIP", True))
            hip_for_radiuss_projects(entries, spec, compiler)
        else:
            entries.append(cmake_cache_option("ENABLE_HIP", False))

        return entries

    def initconfig_package_entries(self):
        spec = self.spec
        entries = []

        option_prefix = "RAJA_" if spec.satisfies("@0.14.0:") else ""

        # TPL locations
        entries.append("#------------------{0}".format("-" * 60))
        entries.append("# TPLs")
        entries.append("#------------------{0}\n".format("-" * 60))

        entries.append(cmake_cache_path("BLT_SOURCE_DIR", spec["blt"].prefix))
        if "camp" in self.spec:
            entries.append(cmake_cache_path("camp_DIR", spec["camp"].prefix))

        # Build options
        entries.append("#------------------{0}".format("-" * 60))
        entries.append("# Build Options")
        entries.append("#------------------{0}\n".format("-" * 60))

        entries.append(cmake_cache_string(
            "CMAKE_BUILD_TYPE", spec.variants["build_type"].value))
        entries.append(cmake_cache_option("BUILD_SHARED_LIBS", "+shared" in spec))

        entries.append(cmake_cache_option("RAJA_ENABLE_DESUL_ATOMICS", "+desul" in spec))

        entries.append(cmake_cache_option("RAJA_ENABLE_VECTORIZATION", "+vectorization" in spec))

        if "+desul" in spec:
            entries.append(cmake_cache_string("BLT_CXX_STD","c++14"))
            if "+cuda" in spec:
                entries.append(cmake_cache_string("CMAKE_CUDA_STANDARD", "14"))

        entries.append(
            cmake_cache_option("{}ENABLE_EXAMPLES".format(option_prefix), "+examples" in spec)
        )
        if spec.satisfies("@0.14.0:"):
            entries.append(
                cmake_cache_option(
                    "{}ENABLE_EXERCISES".format(option_prefix), "+exercises" in spec
                )
            )
        else:
            entries.append(cmake_cache_option("ENABLE_EXERCISES", "+exercises" in spec))

        ### #TODO: Treat the workaround when building tests with spack wrapper
        ### #      For now, removing it to test CI, which builds tests outside of wrapper.
        ### # Work around spack adding -march=ppc64le to SPACK_TARGET_ARGS which
        ### # is used by the spack compiler wrapper.  This can go away when BLT
        ### # removes -Werror from GTest flags
        ### if self.spec.satisfies("%clang target=ppc64le:") or ( not self.run_tests and not "+tests" in spec):
        if not self.run_tests and not "+tests" in spec:
            entries.append(cmake_cache_option("ENABLE_TESTS", False))
        else:
            entries.append(cmake_cache_option("ENABLE_TESTS", True))

        entries.append(cmake_cache_option("RAJA_HOST_CONFIG_LOADED", True))

        return entries

    def cmake_args(self):
        options = []
        return options

    @property
    def build_relpath(self):
        """Relative path to the cmake build subdirectory."""
        return join_path("..", self.build_dirname)

    @run_after("install")
    def setup_build_tests(self):
        """Copy the build test files after the package is installed to a
        relative install test subdirectory for use during `spack test run`."""
        # Now copy the relative files
        self.cache_extra_test_sources(self.build_relpath)

        # Ensure the path exists since relying on a relative path at the
        # same level as the normal stage source path.
        mkdirp(self.install_test_root)

    @property
    def _extra_tests_path(self):
        # TODO: The tests should be converted to re-build and run examples
        # TODO: using the installed libraries.
        return join_path(self.install_test_root, self.build_relpath, "bin")

    def _test_examples(self):
        """Perform very basic checks on a subset of copied examples."""
        checks = [
            (
                "ex5_line-of-sight_solution",
                [r"RAJA sequential", r"RAJA OpenMP", r"result -- PASS"],
            ),
            (
                "ex6_stencil-offset-layout_solution",
                [r"RAJA Views \(permuted\)", r"result -- PASS"],
            ),
            (
                "ex8_tiled-matrix-transpose_solution",
                [r"parallel top inner loop", r"collapsed inner loops", r"result -- PASS"],
            ),
            ("kernel-dynamic-tile", [r"Running index", r"(24,24)"]),
            ("plugin-example", [r"Launching host kernel for the 10 time"]),
            ("tut_batched-matrix-multiply", [r"result -- PASS"]),
            ("wave-eqn", [r"Max Error = 2", r"Evolved solution to time"]),
        ]
        for exe, expected in checks:
            reason = "test: checking output of {0} for {1}".format(exe, expected)
            self.run_test(
                exe,
                [],
                expected,
                installed=False,
                purpose=reason,
                skip_missing=True,
                work_dir=self._extra_tests_path,
            )

    def test(self):
        """Perform smoke tests."""
        self._test_examples()
