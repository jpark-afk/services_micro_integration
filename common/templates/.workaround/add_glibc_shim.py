#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""Inject optional glibc 2.38 symbol shim sources into generated CMakeLists.

Safe no-op when already injected.
"""

from __future__ import annotations

import argparse
from pathlib import Path

SHIM_C = """#if defined(__linux__) && defined(__GLIBC__)
#include <stdlib.h>

__attribute__((weak)) unsigned long long __isoc23_strtoull(const char *nptr, char **endptr, int base) { return strtoull(nptr, endptr, base); }
__attribute__((weak)) unsigned long __isoc23_strtoul(const char *nptr, char **endptr, int base) { return strtoul(nptr, endptr, base); }
__attribute__((weak)) long long __isoc23_strtoll(const char *nptr, char **endptr, int base) { return strtoll(nptr, endptr, base); }
__attribute__((weak)) long __isoc23_strtol(const char *nptr, char **endptr, int base) { return strtol(nptr, endptr, base); }

#if defined(__GNUC__) && defined(__ELF__)
unsigned long long __isoc23_strtoull_glibc238(const char *nptr, char **endptr, int base) __attribute__((alias("__isoc23_strtoull")));
unsigned long __isoc23_strtoul_glibc238(const char *nptr, char **endptr, int base) __attribute__((alias("__isoc23_strtoul")));
long long __isoc23_strtoll_glibc238(const char *nptr, char **endptr, int base) __attribute__((alias("__isoc23_strtoll")));
long __isoc23_strtol_glibc238(const char *nptr, char **endptr, int base) __attribute__((alias("__isoc23_strtol")));

__asm__(".symver __isoc23_strtoull_glibc238,__isoc23_strtoull@GLIBC_2.38");
__asm__(".symver __isoc23_strtoul_glibc238,__isoc23_strtoul@GLIBC_2.38");
__asm__(".symver __isoc23_strtoll_glibc238,__isoc23_strtoll@GLIBC_2.38");
__asm__(".symver __isoc23_strtol_glibc238,__isoc23_strtol@GLIBC_2.38");
#endif
#else
typedef int isoc23_strtoull_shim_unused;
#endif
"""

SHIM_BLOCK = """
# BEGIN isoc23 shim injection
set(ISOC23_SHIM_SRC ${CMAKE_CURRENT_SOURCE_DIR}/isoc23_strtoull_shim.c)
foreach(_shim_target IN ITEMS
        testapp_system_publisher
        testapp_system_subscriber
        testapp_system_dpse_publisher
        testapp_system_dpse_subscriber)
    if(TARGET ${_shim_target})
        target_sources(${_shim_target} PRIVATE ${ISOC23_SHIM_SRC})
    endif()
endforeach()
# END isoc23 shim injection
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmakelists", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    cmake_path = Path(args.cmakelists)
    outdir = Path(args.outdir)
    shim_path = outdir / "isoc23_strtoull_shim.c"

    if not shim_path.exists():
        shim_path.write_text(SHIM_C, encoding="utf-8", newline="\n")

    text = cmake_path.read_text(encoding="utf-8")
    if "# BEGIN isoc23 shim injection" not in text:
        cmake_path.write_text(text + SHIM_BLOCK, encoding="utf-8", newline="\n")
        print(f"patched: {cmake_path}")
    else:
        print(f"no changes: {cmake_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
