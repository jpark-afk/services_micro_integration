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

RTIMEHOME="/home/jpark/dds/rti_connext_dds_micro-4.3.0_ER738"
RTIMEHOME="${RTIMEHOME/#\~/$HOME}"
export RTIMEHOME

XML_DIR="./user_work"
RTIME_MAG_FILES="test_system.xml"
JRE_HOME="/usr/lib/jvm/default-java"
export JRE_HOME

TARGET_NAME="x86_64leElfgcc13.3.0-Linux6"
BUILD_CONFIG="Debug"
GENERATOR="Unix Makefiles"
SRC_DIR="./testapp"
SCHEMA_PATH="${RTIMEHOME}/rtiddsmag/resource/schema/dds-xml_system_definitions.xsd"

if [[ ! -d "${SRC_DIR}" ]]; then exit 1; fi
if [[ ! -f "${XML_DIR}/${RTIME_MAG_FILES}" ]]; then exit 1; fi
if [[ "${RTIME_MAG_FILES}" == */* ]]; then exit 1; fi
if [[ ! -f "${SCHEMA_PATH}" ]]; then
    echo "ERROR: DDS System XML schema not found: ${SCHEMA_PATH}"
    exit 1
fi
if ! grep -q 'xsi:noNamespaceSchemaLocation=' "${XML_DIR}/${RTIME_MAG_FILES}"; then
    echo "ERROR: xsi:noNamespaceSchemaLocation not found in ${XML_DIR}/${RTIME_MAG_FILES}"
    exit 1
fi

STAGED_XML=0
if [[ ! -f "${SRC_DIR}/${RTIME_MAG_FILES}" ]]; then STAGED_XML=1; fi
sed -E "s#xsi:noNamespaceSchemaLocation=\"[^\"]*\"#xsi:noNamespaceSchemaLocation=\"${SCHEMA_PATH}\"#" \
    "${XML_DIR}/${RTIME_MAG_FILES}" > "${SRC_DIR}/${RTIME_MAG_FILES}"

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