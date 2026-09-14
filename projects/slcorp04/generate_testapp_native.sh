#!/usr/bin/env bash
set -euo pipefail

if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    echo "Do not 'source' this script. Run it as: ./generate_testapp_native.sh or: bash generate_testapp_native.sh"
    return 0
fi

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
JRE_HOME="/usr/lib/jvm/default-java"
export JRE_HOME
SYSTEM_XML_PATH="${SCRIPT_DIR}/./user_work/test_system.xml"
IS_DPSE="YES"
MAG_APPLICATION_TYPE="micro4"
OUTPUT="testapp"
MAG_DEPLOYMENT="GCS_LEFT_2_Domain_6_Deployment"
COMMON_TEMPLATES_DIR="..\..\common\templates"
COMMON_TEMPLATES_DIR="${COMMON_TEMPLATES_DIR//\\//}"
MAG_TEMPLATE_PATH="${SCRIPT_DIR}/${COMMON_TEMPLATES_DIR}/.workaround"
SCHEMA_PATH="${RTIMEHOME}/rtiddsmag/resource/schema/dds-xml_system_definitions.xsd"

RTIDDSMAG="${RTIMEHOME}/bin/rtiddsmag"
if [[ ! -x "${RTIDDSMAG}" ]]; then
    RTIDDSMAG="${RTIMEHOME}/rtiddsmag/scripts/rtiddsmag"
fi

RTIDDSGEN="${RTIMEHOME}/bin/rtiddsgen"
if [[ ! -x "${RTIDDSGEN}" ]]; then
    RTIDDSGEN="${RTIMEHOME}/rtiddsgen/scripts/rtiddsgen"
fi

if [[ ! -f "${SYSTEM_XML_PATH}" ]]; then
    echo "ERROR: DDS System XML not found: ${SYSTEM_XML_PATH}"
    exit 1
fi

if [[ ! -x "${RTIDDSMAG}" ]]; then
    echo "ERROR: rtiddsmag not found or not executable under RTIMEHOME: ${RTIMEHOME}"
    exit 1
fi

if [[ ! -x "${RTIDDSGEN}" ]]; then
    echo "ERROR: rtiddsgen not found or not executable under RTIMEHOME: ${RTIMEHOME}"
    exit 1
fi
if [[ ! -f "${SCHEMA_PATH}" ]]; then
    echo "ERROR: DDS System XML schema not found: ${SCHEMA_PATH}"
    exit 1
fi
if ! grep -q 'xsi:noNamespaceSchemaLocation=' "${SYSTEM_XML_PATH}"; then
    echo "ERROR: xsi:noNamespaceSchemaLocation not found in ${SYSTEM_XML_PATH}"
    exit 1
fi

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "ERROR: python3/python was not found on PATH."
    exit 1
fi

mkdir -p "${OUTPUT}"
find "${OUTPUT}" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

XML_FILE="$(basename "${SYSTEM_XML_PATH}")"
XML_NAME="${XML_FILE%.*}"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT
TOOL_XML="${TEMP_DIR}/${XML_FILE}"

sed -E "s#xsi:noNamespaceSchemaLocation=\"[^\"]*\"#xsi:noNamespaceSchemaLocation=\"${SCHEMA_PATH}\"#" \
    "${SYSTEM_XML_PATH}" > "${TOOL_XML}"

echo "[1/5] Running rtiddsmag..."
"${RTIDDSMAG}" \
    -inputXml "${TOOL_XML}" \
    -deployment "${MAG_DEPLOYMENT}" \
    -applicationType "${MAG_APPLICATION_TYPE}" \
    -language C \
    -d "${OUTPUT}" \
    -replace

echo "[2/5] Running rtiddsgen..."
"${RTIDDSGEN}" \
    -language C \
    -create typefiles -micro -ppDisable \
    "${TOOL_XML}" \
    -d "${OUTPUT}"

echo "[3/5] Flattening \"${OUTPUT}\"..."
OUTPUT_ABS="$(cd "${OUTPUT}" && pwd)"
find "${OUTPUT}" -mindepth 2 -type f -exec mv -f -t "${OUTPUT_ABS}" -- {} +
find "${OUTPUT}" -mindepth 1 -depth -type d -empty -delete

echo "[4/5] Copying \"${SYSTEM_XML_PATH}\" into \"${OUTPUT}\"..."
cp -f "${TOOL_XML}" "${OUTPUT_ABS}/${XML_FILE}"

if [[ "${IS_DPSE}" == "YES" ]]; then
    echo "[5/5] DPSE Appgen patch..."
    DPSE_TEMP_DIR="${OUTPUT}/dpse_appgen_temp"
    mkdir -p "${DPSE_TEMP_DIR}"
    "${RTIDDSMAG}" \
        -inputXml "${TOOL_XML}" \
        -language C \
        -d "${DPSE_TEMP_DIR}" \
        -replace
    "${PYTHON_BIN}" "${MAG_TEMPLATE_PATH}/patch_dpse_appgen.py" --xml-name "${XML_NAME}" --origin-dir "${OUTPUT}" --temp-dir "${DPSE_TEMP_DIR}" --takeall
    rm -rf "${DPSE_TEMP_DIR}"
fi

echo "Done. Generated files are under \"${OUTPUT}\"."