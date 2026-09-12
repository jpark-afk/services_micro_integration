#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""Patch DPSE-mode Appgen.h/.c files with the correct include and dds_ prefix.

rtiddsmag run without -deployment/-applicationType produces <xmlName>Appgen.h/.c
that (a) #include the wrong header for the type plugin, and (b) reference
"<TypeName>TypePlugin_get" instead of "dds_<TypeName>TypePlugin_get".

This copies the temp-generated files over the originally-generated
(-deployment/-applicationType) Appgen.h/.c, fixing both issues along the way.
"""
import argparse
import os
import re
import sys

TYPE_PLUGIN_GET_RE = re.compile(r"\b\w+TypePlugin_get\b")


def fix_type_plugin_get(text):
    def repl(match):
        token = match.group(0)
        return token if token.startswith("dds_") else "dds_" + token

    return TYPE_PLUGIN_GET_RE.sub(repl, text)


def first_include_line(text):
    for line in text.splitlines():
        if line.strip().startswith("#include"):
            return line
    return None


def fix_types_plugin_include(temp_text, origin_text):
    origin_include = first_include_line(origin_text)
    temp_include = first_include_line(temp_text)
    if origin_include is None or temp_include is None:
        print("WARNING: could not locate #include line; skipping include fix.", file=sys.stderr)
        return temp_text
    return temp_text.replace(temp_include, origin_include, 1)


def patch_file(temp_path, origin_path, fix_include, takeall=False):
    with open(temp_path, "r", encoding="utf-8") as f:
        temp_text = f.read()

    if not takeall:
        if fix_include:
            with open(origin_path, "r", encoding="utf-8") as f:
                origin_text = f.read()
            temp_text = fix_types_plugin_include(temp_text, origin_text)

        temp_text = fix_type_plugin_get(temp_text)

    with open(origin_path, "w", encoding="utf-8") as f:
        f.write(temp_text)
    print("Patched: %s" % origin_path, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-name", required=True, help="XML base name, e.g. dds_system")
    parser.add_argument("--origin-dir", required=True, help="Directory containing the original <xmlName>Appgen.h/.c (dds_impl)")
    parser.add_argument("--temp-dir", required=True, help="Directory containing the freshly-generated <xmlName>Appgen.h/.c")
    parser.add_argument("--takeall", action="store_true", help="Overwrite origin files with temp files as-is, skipping include/TypePlugin_get fixes")
    args = parser.parse_args()

    header_name = args.xml_name + "Appgen.h"
    source_name = args.xml_name + "Appgen.c"

    temp_h = os.path.join(args.temp_dir, header_name)
    temp_c = os.path.join(args.temp_dir, source_name)
    origin_h = os.path.join(args.origin_dir, header_name)
    origin_c = os.path.join(args.origin_dir, source_name)

    for path in (temp_h, temp_c, origin_h, origin_c):
        if not os.path.isfile(path):
            print("ERROR: file not found: %s" % path, file=sys.stderr)
            return 1

    patch_file(temp_h, origin_h, fix_include=True, takeall=args.takeall)
    patch_file(temp_c, origin_c, fix_include=False, takeall=args.takeall)
    return 0


if __name__ == "__main__":
    sys.exit(main())
