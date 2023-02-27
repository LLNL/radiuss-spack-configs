# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import glob
import socket
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



class Chai(CachedCMakePackage, CudaPackage, ROCmPackage):
    """
    Copy-hiding array interface for data migration between memory spaces
    """

    homepage = "https://github.com/LLNL/CHAI"
    git = "https://github.com/LLNL/CHAI.git"
    tags = ["ecp", "e4s", "radiuss"]

    maintainers = ["davidbeckingsale"]

    version("develop", branch="develop", submodules=False)
    version("main", branch="main", submodules=False)
    version("2022.10.0", tag="v2022.10.0", submodules=False)
    version("2022.03.0", tag="v2022.03.0", submodules=False)
    version("2.4.0", tag="v2.4.0", submodules=True)
    version("2.3.0", tag="v2.3.0", submodules=True)
    version("2.2.2", tag="v2.2.2", submodules=True)
    version("2.2.1", tag="v2.2.1", submodules=True)
    version("2.2.0", tag="v2.2.0", submodules=True)
    version("2.1.1", tag="v2.1.1", submodules=True)
    version("2.1.0", tag="v2.1.0", submodules=True)
    version("2.0.0", tag="v2.0.0", submodules=True)
    version("1.2.0", tag="v1.2.0", submodules=True)
    version("1.1.0", tag="v1.1.0", submodules=True)
    version("1.0", tag="v1.0", submodules=True)

    variant("enable_pick", default=False, description="Enable pick method")
    variant("shared", default=True, description="Build Shared Libs")
    variant("raja", default=False, description="Build plugin for RAJA")
    variant("examples", default=True, description="Build examples.")
    variant("openmp", default=False, description="Build using OpenMP")
    # TODO: figure out gtest dependency and then set this default True
    # and remove the +tests conflict below.
    variant(
        "tests",
        default="none",
        values=("none", "basic", "benchmarks"),
        multi=False,
        description="Tests to run",
    )

    depends_on("cmake@3.8:", type="build")
    depends_on("cmake@3.9:", type="build", when="+cuda")
    depends_on("cmake@3.14:", type="build", when="@2022.03.0:")

    depends_on("blt@0.5.2:", type="build", when="@2022.10.0:")
    depends_on("blt@0.5.0:", type="build", when="@2022.03.0:")
    depends_on("blt@0.4.1:", type="build", when="@2.4.0:")
    depends_on("blt@0.4.0:", type="build", when="@2.3.0")
    depends_on("blt@0.3.6:", type="build", when="@:2.2.2")

    depends_on("umpire")
    depends_on("umpire@2022.10.0:", when="@2022.10.0:")
    depends_on("umpire@2022.03.0:", when="@2022.03.0:")
    depends_on("umpire@6.0.0", when="@2.4.0")
    depends_on("umpire@4.1.2", when="@2.2.0:2.3.0")
    depends_on("umpire@main", when="@main")

    with when("+cuda"):
        depends_on("umpire+cuda")
        for sm_ in CudaPackage.cuda_arch_values:
            depends_on("umpire+cuda cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    with when("+rocm"):
        depends_on("umpire+rocm")
        for arch in ROCmPackage.amdgpu_targets:
            depends_on(
                "umpire+rocm amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch)
            )

    with when("+raja"):
        depends_on("raja~openmp", when="~openmp")
        depends_on("raja+openmp", when="+openmp")
        depends_on("raja@0.14.0", when="@2.4.0")
        depends_on("raja@0.13.0", when="@2.3.0")
        depends_on("raja@0.12.0", when="@2.2.0:2.2.2")
        depends_on("raja@2022.03.0:", when="@2022.03.0:")
        depends_on("raja@2022.10.0:", when="@2022.10.0:")
        depends_on("raja@main", when="@main")

        with when("+cuda"):
            depends_on("raja+cuda")
            for sm_ in CudaPackage.cuda_arch_values:
                depends_on("raja+cuda cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))
        with when("+rocm"):
            depends_on("raja+rocm")
            for arch in ROCmPackage.amdgpu_targets:
                depends_on(
                    "raja+rocm amdgpu_target={0}".format(arch),
                    when="amdgpu_target={0}".format(arch),
                )

    def _get_sys_type(self, spec):
        sys_type = spec.architecture
        if "SYS_TYPE" in env:
            sys_type = env["SYS_TYPE"]
        return sys_type

    @property
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
        entries = super(Chai, self).initconfig_compiler_entries()

        # adrienbernede-22-11:
        #   This was in upstream Spack raja package, but it’s causing the follwing failure Umpire:
        #     CMake Error in src/umpire/CMakeLists.txt:
        #     No known features for CXX compiler
        #
        #   In CHAI, we see another error:
        #       [ 15%] Linking C executable ../../../tests/blt_hip_runtime_c_smoke
        #       clang (LLVM option parsing): for the --amdgpu-early-inline-all option: may only occur zero or one times!
        #       clang (LLVM option parsing): for the --amdgpu-function-calls option: may only occur zero or one times!
        #   We suspect this error comes from the use of hip compiler here, so we comment it:
        #
        #if "+rocm" in spec:
        #    entries.insert(0, cmake_cache_path("CMAKE_CXX_COMPILER", spec["hip"].hipcc))

        blt_link_helpers(entries, spec, compiler)

        return entries

    def initconfig_hardware_entries(self):
        spec = self.spec
        compiler = self.compiler
        entries = super(Chai, self).initconfig_hardware_entries()

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

        option_prefix = "CHAI_" if spec.satisfies("@2022.03.0:") else ""

        # TPL locations
        entries.append("#------------------{0}".format("-" * 60))
        entries.append("# TPLs")
        entries.append("#------------------{0}\n".format("-" * 60))

        entries.append(cmake_cache_path(
            "BLT_SOURCE_DIR", spec["blt"].prefix))
        if "+raja" in spec:
            entries.append(cmake_cache_option(
                "{}ENABLE_RAJA_PLUGIN".format(option_prefix), True))
            entries.append(cmake_cache_path(
                "RAJA_DIR", spec["raja"].prefix))
        entries.append(cmake_cache_path(
            "umpire_DIR", spec["umpire"].prefix))

        # Build options
        entries.append("#------------------{0}".format("-" * 60))
        entries.append("# Build Options")
        entries.append("#------------------{0}\n".format("-" * 60))

        # Build options
        entries.append(cmake_cache_string(
            "CMAKE_BUILD_TYPE", spec.variants["build_type"].value))
        entries.append(cmake_cache_option(
            "BUILD_SHARED_LIBS", "+shared" in spec))

        # Generic options that have a prefixed equivalent in CHAI CMake
        entries.append(cmake_cache_option(
            "ENABLE_OPENMP", "+openmp" in spec))
        entries.append(cmake_cache_option(
            "ENABLE_EXAMPLES", "+examples" in spec))
        entries.append(cmake_cache_option(
            "ENABLE_DOCS", False))
        if "tests=benchmarks" in spec:
            # BLT requires ENABLE_TESTS=True to enable benchmarks
            entries.append(cmake_cache_option(
                "ENABLE_BENCHMARKS", True))
            entries.append(cmake_cache_option(
                "ENABLE_TESTS", True))
        else:
            entries.append(cmake_cache_option(
                "ENABLE_TESTS", "tests=none" not in spec))

        # Prefixed options that used to be name without one
        entries.append(cmake_cache_option(
            "{}ENABLE_PICK".format(option_prefix), "+enable_pick" in spec))

        return entries

    def cmake_args(self):
        options = []
        return options
