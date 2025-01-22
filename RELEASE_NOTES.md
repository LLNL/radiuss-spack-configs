# v2024.x.x

Recommended Spack version:

## Packages Update
- Update Care package with 0.14.x releases and C++17 requirements.
- Fix sycl setup in RAJAPerf.
- Update external specs with latest available version on each machine.
- Make config more consistent with what Axom is using (goal: build axom with RSC).
- Add rocrand, rocsparse, rocthurst for hypre builds.
- Add lowopttest variant in RAJA and RAJAPerf for Intel CI checks

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
