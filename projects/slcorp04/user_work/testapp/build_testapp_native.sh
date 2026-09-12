#!/usr/bin/env bash
set -euo pipefail

# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.

if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    echo "Do not 'source' this script. Run it as: ./build_testapp_native.sh or: bash build_testapp_native.sh"
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
RTIMEHOME="/home/jpark/Documents/dds/rti_connext_dds_micro-4.3.0"
RTIMEHOME="${RTIMEHOME/#\~/$HOME}"
export RTIMEHOME

# Java runtime root used by RTI tooling. Keep aligned with ../build_testapp_native.sh.
JRE_HOME="/usr/lib/jvm/default-java"
export JRE_HOME

RTIME_TARGET_NAME="x86_64leElfgcc13.3.0-Linux6"
export RTIME_TARGET_NAME

BUILD_CONFIG="Release"
GENERATOR="Unix Makefiles"
BUILD_DIR="${SCRIPT_DIR}/native_build"
APPLICATION_DIR="${SCRIPT_DIR}/native_output/MyDeploymentLib/MyDeploymentScenario/GCS_LEFT_2_Domain_6_Deployment/GCS_LEFT_2_Domain_6_Application"
APPLICATION_EXE="${APPLICATION_DIR}/objs/${RTIME_TARGET_NAME}/GCS_LEFT_2_Domain_6_Application"

# Rebuild RTI PSL locally when ABI mismatch is detected (YES or NO).
AUTO_REBUILD_PSL="${AUTO_REBUILD_PSL:-YES}"

# ============================================================
# Pre-checks
# ============================================================
if [[ ! -f "${APPLICATION_DIR}/CMakeLists.txt" ]]; then
    echo "Generated application CMakeLists.txt not found: ${APPLICATION_DIR}/CMakeLists.txt"
    echo "Run generate_testapp_native.bat on Windows or the equivalent Linux generation flow first."
    exit 1
fi

if ! command -v cmake >/dev/null 2>&1; then
    echo "cmake was not found on PATH."
    exit 1
fi

if [[ ! -d "${RTIMEHOME}" ]]; then
    echo "RTIMEHOME not found: ${RTIMEHOME}"
    exit 1
fi

glibc_version() {
    local version
    version="$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')"
    if [[ -z "${version}" ]]; then
        version="$(ldd --version 2>/dev/null | head -n1 | awk '{print $NF}')"
    fi
    echo "${version}"
}

version_lt() {
    local lhs rhs
    lhs="${1}"
    rhs="${2}"
    [[ "$(printf '%s\n%s\n' "${lhs}" "${rhs}" | sort -V | head -n1)" != "${rhs}" ]]
}

LOCAL_GLIBC="$(glibc_version)"
if [[ "${RTIME_TARGET_NAME}" == "x86_64leElfgcc13.3.0-Linux6" && -n "${LOCAL_GLIBC}" ]] && version_lt "${LOCAL_GLIBC}" "2.38"; then
    echo "Detected glibc ${LOCAL_GLIBC}, but ${RTIME_TARGET_NAME} prebuilt PSL expects glibc >= 2.38."
    PSL_MARKER="${RTIMEHOME}/lib/${RTIME_TARGET_NAME}/.rebuilt_for_glibc_${LOCAL_GLIBC}_${BUILD_CONFIG}"
    find_rebuilt_ospsl() {
        find "${RTIMEHOME}/lib/${RTIME_TARGET_NAME}" -maxdepth 2 -type f -name 'librti_me_ospsl*.a' 2>/dev/null | head -n1
    }
    PSL_LIB="$(find_rebuilt_ospsl)"
    if [[ "${AUTO_REBUILD_PSL}" == "YES" ]]; then
        if [[ -f "${PSL_MARKER}" && -f "${PSL_LIB}" ]]; then
            echo "PSL rebuild already completed for glibc ${LOCAL_GLIBC}; using ${RTIME_TARGET_NAME}."
        else
            echo "Rebuilding RTI PSL locally for this host glibc..."
            "${RTIMEHOME}/resource/scripts/rtime-make" \
                --config "${BUILD_CONFIG}" \
                --build \
                --target "${RTIME_TARGET_NAME}" \
                -G "${GENERATOR}"
            mkdir -p "${RTIMEHOME}/lib/${RTIME_TARGET_NAME}"
            PSL_LIB="$(find_rebuilt_ospsl)"
            if [[ ! -f "${PSL_LIB}" ]]; then
                echo "Expected rebuilt PSL archive not found under: ${RTIMEHOME}/lib/${RTIME_TARGET_NAME}"
                exit 2
            fi
            : > "${PSL_MARKER}"
        fi
        echo "Using rebuilt RTI target: ${RTIME_TARGET_NAME}"
    else
        echo "Set AUTO_REBUILD_PSL=YES in this script, then re-run."
        echo "Or run manually:"
        echo "  ${RTIMEHOME}/resource/scripts/rtime-make --config ${BUILD_CONFIG} --build --target ${RTIME_TARGET_NAME} -G '${GENERATOR}'"
        exit 2
    fi
fi

# ============================================================
# Build with CMake
# ============================================================
echo "Configuring ${APPLICATION_DIR}..."
cmake -S "${APPLICATION_DIR}" \
    -B "${BUILD_DIR}" \
    -G "${GENERATOR}" \
    -DCMAKE_BUILD_TYPE="${BUILD_CONFIG}" \
    -DRTIMEHOME="${RTIMEHOME}" \
    -DRTIME_TARGET_NAME="${RTIME_TARGET_NAME}"

echo "Building ${BUILD_CONFIG}..."
cmake --build "${BUILD_DIR}" --config "${BUILD_CONFIG}" --parallel

echo "Done. Executable should be under:"
echo "${APPLICATION_EXE}"