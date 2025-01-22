# v2025.01.0

Recommended Spack version: develop-2025-01-12

## Packages Update
- Update Care package with 0.14.x releases and C++17 requirements.
- Update sycl
- Split spack environment file in separate files (access packages.yaml and compilers.yaml directly)
- Update external specs with latest available version on each machine.
- Make config more consistent with what Axom is using (goal: build axom with RSC).
- Add rocrand, rocsparse, rocthurst for hypre builds.
- Add lowopttest variant in RAJA and RAJAPerf for Intel CI checks
- Apply workarounds to enforce using a single compiler for a packages and its dependencies
- Update rocm tioga toolchain: add rocm 6.3.0, remove rocm 5.4.1, 5.7.0 and 6.1.1
- Add compiler rpaths when necessary (mimics LC wrappers, prevent from tweaking spack packages)
- Rename intel to oneapi when relevant
- Sync with Spack@develop of January 12 2025

## Configs Update
- Use llvm-amdgpu to determine ROCM_PATH (utility function in camp package).
- Add intel 2024.

## Shared CI jobs

# v2024.09.0

Recommended Spack version: develop-2024-10-06

## Packages Update
- Add 2024.07 versions to packages
- Turn CARE and Caliper into CachedCMakePackages
- Improve coherency in version constraints
- Various updates from upstream Spack.

## Configs Update
- Add rocm 6.2.0 on Tioga
- Drop rocm 5.7.0 in favor of 5.7.1 on corona
- Enforce coherency between rocm software stack and compiler

## Shared CI jobs
- Remove XL jobs
