#!/usr/bin/env python3
"""Patch DDS XML primitive type names for rtiarcgen compatibility.

The source XML may use the newer type names from
rti_dds_topic_types_definitions.xsd. Some rtiarcgen paths still resolve the
deprecated IDL-style names correctly, so this script writes a patched copy for
rtiarcgen without modifying the original XML.
"""
import argparse
import os
import re
import sys


TYPE_MAP = {
    "uint8": "octet",
    "uint16": "unsignedShort",
    "uint32": "unsignedLong",
    "uint64": "unsignedLongLong",
    "int8": "octet",
    "int16": "short",
    "int32": "long",
    "int64": "longLong",
    "float32": "float",
    "float64": "double",
    "float128": "longDouble",
}


def patch(xml_path, output_path=None):
    base, ext = os.path.splitext(xml_path)
    patch_path = output_path or (base + "_arcgen_patch" + ext)

    with open(xml_path, "r", encoding="utf-8") as xml_file:
        content = xml_file.read()

    changed = []
    pattern = re.compile(r'(\btype\s*=\s*["\'])([^"\']+)(["\'])')

    def replace_type(match):
        type_name = match.group(2)
        if type_name not in TYPE_MAP:
            return match.group(0)
        new_type = TYPE_MAP[type_name]
        changed.append((type_name, new_type))
        return match.group(1) + new_type + match.group(3)

    patched_content = pattern.sub(replace_type, content)

    with open(patch_path, "w", encoding="utf-8", newline="") as patch_file:
        patch_file.write(patched_content)

    if changed:
        summary = {}
        for old_type, new_type in changed:
            summary[(old_type, new_type)] = summary.get((old_type, new_type), 0) + 1
        for (old_type, new_type), count in sorted(summary.items()):
            print("%s -> %s: %d" % (old_type, new_type, count), file=sys.stderr)
        print("Patched %d type reference(s)." % len(changed), file=sys.stderr)
    else:
        print("No rtiarcgen type workaround changes needed.", file=sys.stderr)

    print("Saved: %s" % patch_path, file=sys.stderr)
    return patch_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", required=True, help="Path to DDS System XML")
    parser.add_argument("--out", help="Path for patched XML output")
    args = parser.parse_args()

    if not os.path.isfile(args.xml):
        print("ERROR: file not found: %s" % args.xml, file=sys.stderr)
        return 1

    patch_path = patch(args.xml, args.out)
    print(patch_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())