# v2025.10.0

Recommended Spack version: v1.0.2
Vetted spack-packages commit: a3806d96d2

## Machine Changes
- Retire Lassen
- Add Matrix for CUDA jobs

## Packages
- Update RAJA CMake requirement to 3.24+ for versions 2025.09.0 and later
- Add CMake 3.25.2 to available external packages

## Configs Update
- Add Matrix machine configuration (toss_4_x86_64_ib)
- Add LLVM 18.1.8 compiler to non-CUDA machines
- Add CUDA externals to Dane (non-GPU machine) for cross-compilation compatibility with Matrix, enabling optimized builds for Matrix architecture

## CI
- Add Matrix to CI pipeline (but turn it off)
- Update CI configurations for Matrix and Dane
- Fix spec list configuration in shared CI environment

# v2025.09.1

Recommended Spack version: v1.0.2
Vetted spack-packages commit: a3806d96d2

## Packages
- Add latest release of some RADIUSS packages.
- Style changes.

## Configs
- Add sycl compiler tied to rocm 6.3.1.

## CI
- Allow to deactivate a CI machine by variable.

# v2025.09.0

Recommended Spack version: 1.0.2:
Vetted spack-packages commit: a3806d96d2

Update Spack configurations to v1 format
- Remove compilers.yaml
- Move compiler definition to packages.yaml
- Create appropriate toolchains
Update most packages with 2025.09 release.
Add support for spack-packages repository set from environment

Retire Ruby

Update CI configuration
Use CI reservation on Dane

Add patches for Caliper

# v2025.06.0

Recommended Spack version: branch rsc-2025-03-0

## Configs Update
- Add rocm 6.4.1 and cce 19.0.0 (cray machines)
- Update gcc to 13.3.1, update mpich to 8.1.32 (cray machines)
- Update cuda to 11.8.0 and add 12.2.0 (cray machines)
- Support running on Dane and Tuolumne
- Check external packages on every machine (expect lassen), update when necessary

## CI
- Replace Poodle with Dane in CI
- Mention CI capabilities in documentation

## Others
- Add utilities to help with spack configs updates
- Improve ordering of externals in packages.yaml files
- Update copyright
- Fix naming convention

# v2025.03.0

Recommended Spack version: branch rsc-2025-03-0

## Add CI
- We add a GitLab CI pipeline leveraging Spack CI to test building some packages with our shared specs.

## Packages Update
- add 2025.03.0 releases for Camp, Umpire, RAJA, CHAI, and 0.15 releases for CARE.
- clean hip support

## Configs Update
- Updated rocm 6.3.0 to 6.3.1 on tioga
- Cleaned older rocm toolchains

## Shared CI jobs
- Updated specs to prepare spack@1.0.0: variants must be applied before compiler

## CI
- Force concretization
- Point at spack internal mirror to reduce firewall traffic

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
