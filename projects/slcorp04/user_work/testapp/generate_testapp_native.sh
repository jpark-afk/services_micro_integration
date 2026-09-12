#!/usr/bin/env bash
set -euo pipefail

# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.

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
}
print_notice

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# ============================================================
# User-configurable variables - edit these for your project
# ============================================================

# Connext Micro 4.3.0 installation root. Keep aligned with ../build_testapp_native.sh.
RTIMEHOME="/home/jpark/Documents/dds/rti_connext_dds_micro-4.3.0_ER738"
RTIMEHOME="${RTIMEHOME/#\~/$HOME}"
export RTIMEHOME

# Java runtime root used by RTI tooling. Keep aligned with ../build_testapp_native.sh.
JRE_HOME="/usr/lib/jvm/default-java"
export JRE_HOME

RTIME_TARGET_NAME="x86_64leElfgcc13.3.0-Linux6"
export RTIME_TARGET_NAME

SYSTEM_XML="gcs_test_system.xml"
OUTPUT_DIR="native_output"
DEPLOYMENT="GCS_LEFT_2_Domain_6_Deployment"
APPLICATION_DIR="native_output/MyDeploymentLib/MyDeploymentScenario/GCS_LEFT_2_Domain_6_Deployment/GCS_LEFT_2_Domain_6_Application"
COMMON_TEMPLATES_DIR="${SCRIPT_DIR}/../../../../common/templates"
MAG_TEMPLATE_PATH="${COMMON_TEMPLATES_DIR}/.workaround"
XML_NAME="${SYSTEM_XML%.xml}"

# Prefer the tool locations used by project scripts; fall back to the paths shown in the MD guide.
RTIDDSMAG="${RTIMEHOME}/bin/rtiddsmag"
if [[ ! -x "${RTIDDSMAG}" ]]; then
    RTIDDSMAG="${RTIMEHOME}/rtiddsmag/scripts/rtiddsmag"
fi

RTIDDSGEN="${RTIMEHOME}/bin/rtiddsgen"
if [[ ! -x "${RTIDDSGEN}" ]]; then
    RTIDDSGEN="${RTIMEHOME}/rtiddsgen/scripts/rtiddsgen"
fi

SCHEMA_PATH="${RTIMEHOME}/rtiddsmag/resource/schema/dds-xml_system_definitions.xsd"

# ============================================================
# Pre-checks
# ============================================================
if [[ ! -f "${SYSTEM_XML}" ]]; then
    echo "DDS System XML not found: ${SCRIPT_DIR}/${SYSTEM_XML}"
    exit 1
fi

if [[ ! -x "${RTIDDSMAG}" ]]; then
    echo "rtiddsmag not found or not executable under RTIMEHOME: ${RTIMEHOME}"
    exit 1
fi

if [[ ! -x "${RTIDDSGEN}" ]]; then
    echo "rtiddsgen not found or not executable under RTIMEHOME: ${RTIMEHOME}"
    exit 1
fi

if [[ ! -f "${SCHEMA_PATH}" ]]; then
    echo "DDS System XML schema not found: ${SCHEMA_PATH}"
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT
TOOL_XML="${TEMP_DIR}/${SYSTEM_XML}"

sed -E "s#xsi:noNamespaceSchemaLocation=\"[^\"]*\"#xsi:noNamespaceSchemaLocation=\"${SCHEMA_PATH}\"#" \
    "${SYSTEM_XML}" > "${TOOL_XML}"

# ============================================================
# Step 1: Generate the deployment-aware Micro C application
# ============================================================
echo "[1/3] Running rtiddsmag for ${DEPLOYMENT}..."
"${RTIDDSMAG}" \
    -inputXml "${TOOL_XML}" \
    -language C \
    -d "${OUTPUT_DIR}" \
    -replace \
    -deployment "${DEPLOYMENT}" \
    -applicationType micro4 \
    -verbosity 3

if [[ ! -d "${APPLICATION_DIR}" ]]; then
    echo "Expected generated application folder not found: ${APPLICATION_DIR}"
    exit 1
fi

# ============================================================
# Step 2: Generate type support beside the MAG-generated sources
# ============================================================
echo "[2/3] Running rtiddsgen type support generation..."
pushd "${RTIMEHOME}/rtiddsmag" > /dev/null
"${RTIDDSGEN}" \
    -create typefiles \
    -micro \
    -language C \
    -interpreted 0 \
    "${TOOL_XML}" \
    -d "${SCRIPT_DIR}/${APPLICATION_DIR}" \
    -replace
popd > /dev/null

# ============================================================
# Step 3: DPSE Appgen patch
# Regenerate Appgen without -deployment/-applicationType so DPSE remote
# participants/endpoints are emitted, then overwrite only Appgen.h/.c.
# ============================================================
echo "[3/3] DPSE Appgen patch..."
DPSE_TEMP_DIR="${SCRIPT_DIR}/${APPLICATION_DIR}/dpse_appgen_temp"
mkdir -p "${DPSE_TEMP_DIR}"

"${RTIDDSMAG}" \
    -inputXml "${TOOL_XML}" \
    -language C \
    -d "${DPSE_TEMP_DIR}" \
    -replace

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "python3/python was not found on PATH."
    exit 1
fi

"${PYTHON_BIN}" "${MAG_TEMPLATE_PATH}/patch_dpse_appgen.py" --xml-name "${XML_NAME}" --origin-dir "${SCRIPT_DIR}/${APPLICATION_DIR}" --temp-dir "${DPSE_TEMP_DIR}" --takeall
rm -rf "${DPSE_TEMP_DIR}"


echo "Done. Generated application is under ${APPLICATION_DIR}."