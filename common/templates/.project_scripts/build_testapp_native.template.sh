#!/usr/bin/env bash
set -euo pipefail

print_notice() {
    echo "[RTI NOTICE] INTERNAL TEMPORARY WORKAROUND"
    echo "[RTI NOTICE] Temporary workaround until an official RTI patch is released."
    echo "[RTI NOTICE] Baseline version: Micro430er738."
    echo "[RTI NOTICE] Not officially supported by RTI Technical Support."
    echo "[RTI NOTICE] Must NOT be applied directly to controller mass-production development."
    echo "[RTI NOTICE] See README.md for details."
}
print_notice

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

RTIMEHOME="@RTIMEHOME_LINUX@"
RTIMEHOME="${RTIMEHOME/#\~/$HOME}"
export RTIMEHOME

XML_DIR="@TEST_XML_DIR_POSIX@"
RTIME_MAG_FILES="@RTIME_MAG_FILES@"
JRE_HOME="@JRE_HOME_LINUX@"
export JRE_HOME

TARGET_NAME="@LINUX_TARGET_NAME@"
BUILD_CONFIG="Debug"
GENERATOR="Unix Makefiles"
SRC_DIR="./testapp"

if [[ ! -d "${SRC_DIR}" ]]; then exit 1; fi
if [[ ! -f "${XML_DIR}/${RTIME_MAG_FILES}" ]]; then exit 1; fi
if [[ "${RTIME_MAG_FILES}" == */* ]]; then exit 1; fi

STAGED_XML=0
if [[ ! -f "${SRC_DIR}/${RTIME_MAG_FILES}" ]]; then STAGED_XML=1; fi
cp -f "${XML_DIR}/${RTIME_MAG_FILES}" "${SRC_DIR}/${RTIME_MAG_FILES}"

pushd "${SRC_DIR}" > /dev/null
set +e
"${RTIMEHOME}/resource/scripts/rtime-make" \
    --config "${BUILD_CONFIG}" \
    --target self \
    --name "${TARGET_NAME}" \
    --build \
    --source-dir . \
    -G "${GENERATOR}" \
    --delete \
    -DRTIME_MAG_FILES="${RTIME_MAG_FILES}"
BUILD_RESULT=$?
set -e
popd > /dev/null

if [[ "${BUILD_RESULT}" -ne 0 ]]; then exit 1; fi
if [[ "${STAGED_XML}" -eq 1 ]]; then rm -f "${SRC_DIR}/${RTIME_MAG_FILES}"; fi

echo "Done. Build output is under ${SRC_DIR}/objs."