# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import glob
import re

from spack.package import *

import llnl.util.tty as tty


def spec_uses_toolchain(spec):
    gcc_toolchain_regex = re.compile(".*gcc-toolchain.*")
    using_toolchain = list(filter(gcc_toolchain_regex.match, spec.compiler_flags["cxxflags"]))
    return using_toolchain

def spec_uses_gccname(spec):
    gcc_name_regex = re.compile(".*gcc-name.*")
    using_gcc_name = list(filter(gcc_name_regex.match, spec.compiler_flags["cxxflags"]))
    return using_gcc_name

def hip_repair_options(options, spec):
    # there is only one dir like this, but the version component is unknown
    options.append(
        "-DHIP_CLANG_INCLUDE_PATH="
        + glob.glob("{}/lib/clang/*/include".format(spec["llvm-amdgpu"].prefix))[0]
    )

def hip_repair_cache(options, spec):
    # there is only one dir like this, but the version component is unknown
    options.append(
        cmake_cache_path(
            "HIP_CLANG_INCLUDE_PATH",
            glob.glob("{}/lib/clang/*/include".format(spec["llvm-amdgpu"].prefix))[0],
        )
    )

def mpi_for_radiuss_projects(options, spec):
    # Machines with cray-mpich have a slurm wrapper arround flux, to use it we
    # duplicate the MPI handling from CachedCMakePackage. This change will be
    # applied directly in the CachedCMakePackage when pushed to upstream Spack.
    if not spec.satisfies("^mpi"):
        return []

    entries = [
        "#------------------{0}".format("-" * 60),
        "# MPI",
        "#------------------{0}\n".format("-" * 60),
    ]

    entries.append(cmake_cache_option("ENABLE_MPI", "+mpi" in spec))

    entries.append(cmake_cache_path("MPI_C_COMPILER", spec["mpi"].mpicc))
    entries.append(cmake_cache_path("MPI_CXX_COMPILER", spec["mpi"].mpicxx))
    entries.append(cmake_cache_path("MPI_Fortran_COMPILER", spec["mpi"].mpifc))

    # Check for slurm
    using_slurm = False
    # RADIUSS Spack Configs change:
    slurm_checks = ["+slurm", "schedulers=slurm", "process_managers=slurm", "cray-mpich"]
    if any(spec["mpi"].satisfies(variant) for variant in slurm_checks):
        using_slurm = True

    # Determine MPIEXEC
    if using_slurm:
        if spec["mpi"].external:
            # Heuristic until we have dependents on externals
            mpiexec = "/usr/bin/srun"
        else:
            mpiexec = os.path.join(spec["slurm"].prefix.bin, "srun")
    else:
        mpiexec = os.path.join(spec["mpi"].prefix.bin, "mpirun")
        if not os.path.exists(mpiexec):
            mpiexec = os.path.join(spec["mpi"].prefix.bin, "mpiexec")

    if not os.path.exists(mpiexec):
        msg = "Unable to determine MPIEXEC, tests may fail"
        entries.append("# {0}\n".format(msg))
        tty.warn(msg)
    else:
        # starting with cmake 3.10, FindMPI expects MPIEXEC_EXECUTABLE
        # vs the older versions which expect MPIEXEC
        if spec["cmake"].satisfies("@3.10:"):
            entries.append(cmake_cache_path("MPIEXEC_EXECUTABLE", mpiexec))
        else:
            entries.append(cmake_cache_path("MPIEXEC", mpiexec))

    # Determine MPIEXEC_NUMPROC_FLAG
    if using_slurm:
        entries.append(cmake_cache_string("MPIEXEC_NUMPROC_FLAG", "-n"))
    else:
        entries.append(cmake_cache_string("MPIEXEC_NUMPROC_FLAG", "-np"))

def hip_for_radiuss_projects(options, spec, compiler):
    # Here is what is typically needed for radiuss projects when building with rocm
    hip_root = spec["hip"].prefix
    rocm_root = hip_root + "/.."
    options.append(cmake_cache_path("HIP_ROOT_DIR", hip_root))
    options.append(cmake_cache_path("ROCM_ROOT_DIR", rocm_root))

    hip_repair_cache(options, spec)

    archs = spec.variants["amdgpu_target"].value
    if archs[0] != "none":
        arch_str = ";".join(archs)
        options.append(cmake_cache_string("CMAKE_HIP_ARCHITECTURES", arch_str))
        options.append(cmake_cache_string("AMDGPU_TARGETS", arch_str))
        options.append(cmake_cache_string("GPU_TARGETS", arch_str))

    # adrienbernede-22-11:
    #   Specific to Umpire, attempt port to RAJA and CHAI
    hip_link_flags = ""
    if "%gcc" in spec or spec_uses_toolchain(spec):
        if "%gcc" in spec:
            gcc_bin = os.path.dirname(compiler.cxx)
            gcc_prefix = os.path.join(gcc_bin, "..")
        else:
            gcc_prefix = spec_uses_toolchain(spec)[0]
        options.append(cmake_cache_string("HIP_CLANG_FLAGS", "--gcc-toolchain={0}".format(gcc_prefix)))
        options.append(cmake_cache_string("CMAKE_EXE_LINKER_FLAGS", hip_link_flags + " -Wl,-rpath {}/lib64".format(gcc_prefix)))
    else:
        options.append(cmake_cache_string("CMAKE_EXE_LINKER_FLAGS", "-Wl,-rpath={0}/llvm/lib/".format(rocm_root)))

def cuda_for_radiuss_projects(options, spec):
    # Here is what is typically needed for radiuss projects when building with cuda

    # CUDA_FLAGS
    cuda_flags = []

    if not spec.satisfies("cuda_arch=none"):
        cuda_archs = ";".join(spec.variants["cuda_arch"].value)
        options.append(cmake_cache_string("CMAKE_CUDA_ARCHITECTURES", cuda_archs))

    if spec_uses_toolchain(spec):
        cuda_flags.append("-Xcompiler {}".format(spec_uses_toolchain(spec)[0]))

    if spec.satisfies("%gcc@8.1: target=ppc64le"):
        cuda_flags.append("-Xcompiler -mno-float128")

    options.append(cmake_cache_string("CMAKE_CUDA_FLAGS", " ".join(cuda_flags)))


class Camp(CMakePackage, CudaPackage, ROCmPackage):
    """
    Compiler agnostic metaprogramming library providing concepts,
    type operations and tuples for C++ and cuda
    """

    homepage = "https://github.com/LLNL/camp"
    git = "https://github.com/LLNL/camp.git"
    url = "https://github.com/LLNL/camp/archive/v0.1.0.tar.gz"

    maintainers("trws")

    license("BSD-3-Clause")

    version("main", branch="main", submodules=False)
    version(
        "2024.02.0",
        tag="v2024.02.0",
        commit="03c80a6c6ab4f97e76a52639563daec71435a277",
        submodules=False,
    )
    version(
        "2023.06.0",
        tag="v2023.06.0",
        commit="ac34c25b722a06b138bc045d38bfa5e8fa3ec9c5",
        submodules=False,
    )
    version("2022.10.1", sha256="2d12f1a46f5a6d01880fc075cfbd332e2cf296816a7c1aa12d4ee5644d386f02")
    version("2022.10.0", sha256="3561c3ef00bbcb61fe3183c53d49b110e54910f47e7fc689ad9ccce57e55d6b8")
    version("2022.03.2", sha256="bc4aaeacfe8f2912e28f7a36fc731ab9e481bee15f2c6daf0cb208eed3f201eb")
    version("2022.03.0", sha256="e9090d5ee191ea3a8e36b47a8fe78f3ac95d51804f1d986d931e85b8f8dad721")
    version("0.3.0", sha256="129431a049ca5825443038ad5a37a86ba6d09b2618d5fe65d35f83136575afdb")
    version("0.2.3", sha256="58a0f3bd5eadb588d7dc83f3d050aff8c8db639fc89e8d6553f9ce34fc2421a7")
    version("0.2.2", sha256="194d38b57e50e3494482a7f94940b27f37a2bee8291f2574d64db342b981d819")
    version("0.1.0", sha256="fd4f0f2a60b82a12a1d9f943f8893dc6fe770db493f8fae5ef6f7d0c439bebcc")

    # TODO: figure out gtest dependency and then set this default True.
    variant("tests", default=False, description="Build tests")
    variant("openmp", default=False, description="Build with OpenMP support")

    depends_on("cub", when="+cuda")

    depends_on("blt", type="build")
    depends_on("blt@0.6.1:", type="build", when="@2024.02.0:")
    depends_on("blt@0.5.0:0.5.3", type="build", when="@2022.03.0:2023.06.0")

    patch("libstdc++-13-missing-header.patch", when="@:2022.10")

    conflicts("^blt@:0.3.6", when="+rocm")

    def cmake_args(self):
        spec = self.spec

        options = []

        options.append("-DBLT_SOURCE_DIR={0}".format(spec["blt"].prefix))

        options.append(self.define_from_variant("ENABLE_CUDA", "cuda"))
        if "+cuda" in spec:
            options.append("-DCUDA_TOOLKIT_ROOT_DIR={0}".format(spec["cuda"].prefix))

            if not spec.satisfies("cuda_arch=none"):
                cuda_arch = spec.variants["cuda_arch"].value
                options.append("-DCMAKE_CUDA_ARCHITECTURES={0}".format(cuda_arch[0]))
                options.append("-DCUDA_ARCH=sm_{0}".format(cuda_arch[0]))
                flag = "-arch sm_{0}".format(cuda_arch[0])
                options.append("-DCMAKE_CUDA_FLAGS:STRING={0}".format(flag))

        options.append(self.define_from_variant("ENABLE_HIP", "rocm"))
        if "+rocm" in spec:
            options.append("-DHIP_ROOT_DIR={0}".format(spec["hip"].prefix))
            hip_repair_options(options, spec)

            archs = self.spec.variants["amdgpu_target"].value
            options.append("-DCMAKE_HIP_ARCHITECTURES={0}".format(archs))
            options.append("-DGPU_TARGETS={0}".format(archs))
            options.append("-DAMDGPU_TARGETS={0}".format(archs))

        options.append(self.define_from_variant("ENABLE_OPENMP", "openmp"))
        options.append(self.define_from_variant("ENABLE_TESTS", "tests"))

        return options
