#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""Patch generated MAG CMakeLists for deterministic build-only mode.

Changes:
- Keep APP_GEN_C/H population when RTIME_SKIP_MAG_REGEN=TRUE.
- Skip rtiddsmag custom regeneration commands when RTIME_SKIP_MAG_REGEN=TRUE.
"""

from __future__ import annotations

import argparse
from pathlib import Path

PREPOPULATE_BLOCK = """IF (DEFINED RTIME_MAG_FILES)
    FOREACH(xml ${RTIME_MAG_FILES})
        GET_FILENAME_COMPONENT(filename ${xml} NAME)
        STRING(REGEX REPLACE "\\\\.xml" "" basename ${filename})
        GET_FILENAME_COMPONENT(basename ${xml} NAME_WE)

        LIST(APPEND APP_GEN_C ${CMAKE_CURRENT_SOURCE_DIR}/${basename}Appgen.c)
        LIST(APPEND APP_GEN_H ${CMAKE_CURRENT_SOURCE_DIR}/${basename}Appgen.h)
    ENDFOREACH()
ENDIF()

IF (DEFINED RTIME_MAG_FILES AND FALSE)
    FOREACH(xml ${RTIME_MAG_FILES})
"""


def patch_text(text: str) -> str:
    updated = text

    # Keep appgen library linkage enabled.
    updated = updated.replace(
        "IF (DEFINED RTIME_MAG_FILES AND FALSE)\n    LIST(APPEND MICRO_C_LIBS rti_me_appgen${RTI_LIB_SUFFIX})",
        "IF (DEFINED RTIME_MAG_FILES)\n    LIST(APPEND MICRO_C_LIBS rti_me_appgen${RTI_LIB_SUFFIX})",
    )

    # Disable only the MAG regeneration custom-command block and preserve
    # pre-generated Appgen.c/Appgen.h in target sources.
    start = "IF (DEFINED RTIME_MAG_FILES)\n    FOREACH(xml ${RTIME_MAG_FILES})"
    if "IF (DEFINED RTIME_MAG_FILES AND FALSE)\n    FOREACH(xml ${RTIME_MAG_FILES})" not in updated and start in updated:
        updated = updated.replace(start, PREPOPULATE_BLOCK, 1)

    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmakelists", required=True)
    args = parser.parse_args()

    cmake_path = Path(args.cmakelists)
    original = cmake_path.read_text(encoding="utf-8")
    patched = patch_text(original)

    if patched != original:
        cmake_path.write_text(patched, encoding="utf-8", newline="\n")
        print(f"patched: {cmake_path}")
    else:
        print(f"no changes: {cmake_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
