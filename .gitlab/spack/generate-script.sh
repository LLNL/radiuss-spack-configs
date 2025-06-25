#! /bin/bash
##############################################################################
# Copyright (c) 2019-2025, Lawrence Livermore National Security, LLC and
# RADIUSS project contributors. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)
##############################################################################

hostname

. ${MY_SPACK_PARENT_DIR}/spack/share/spack/setup-env.sh
spack ${MY_SPACK_DEBUG} env activate --without-view .gitlab/spack/envs/${MY_ENV_NAME}
spack ${MY_SPACK_DEBUG} config blame mirrors
spack ${MY_SPACK_DEBUG} mirror add --oci-username-variable CI_REGISTRY_USER --oci-password-variable CI_REGISTRY_PASSWORD buildcache-destination oci://${CI_REGISTRY_IMAGE}/${SPACK_TARGET}
spack ${MY_SPACK_DEBUG} config blame mirrors
spack ${MY_SPACK_DEBUG} concretize --fresh || spack ${MY_SPACK_DEBUG} concretize --fresh
spack ${MY_SPACK_DEBUG} --color=always --config-scope "${CI_PROJECT_DIR}/.gitlab/spack" ci generate --check-index-only --artifacts-root "${CI_PROJECT_DIR}/jobs_scratch_dir" --output-file "${CI_PROJECT_DIR}/jobs_scratch_dir/pipeline.yml"
cp -rL .gitlab/spack/envs/shared-ci/${LCSCHEDCLUSTER} ${CI_PROJECT_DIR}/jobs_scratch_dir/concrete_environment/${LCSCHEDCLUSTER}
cp -rL .gitlab/spack/envs/shared-ci/spack_repo/llnl/radiuss/repo.yaml ${CI_PROJECT_DIR}/jobs_scratch_dir/concrete_environment/spack_repo/llnl/radiuss/repo.yaml
cp -rL .gitlab/spack/envs/shared-ci/spack_repo/llnl/radiuss/packages ${CI_PROJECT_DIR}/jobs_scratch_dir/concrete_environment/spack_repo/llnl/radiuss/packages
