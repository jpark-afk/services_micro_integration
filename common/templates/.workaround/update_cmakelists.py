#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""
Rewrite the ADD_EXECUTABLE section of the generated CMakeLists.txt AND update
any .vcxproj files under --outdir so that ALL .c/.h files found in --outdir
(directly, not in subdirectories) are registered.

Runs as the final step so it sees the complete set of generated source files.
"""
import argparse
import os
import re
import sys


def update_cmakelists(cmake_path, base, c_files, h_files):
    text = open(cmake_path, "r", encoding="utf-8").read()

    anchor = "SET_LIB_ORDER(MICRO_C_LIBS)"
    idx = text.find(anchor)
    if idx == -1:
        idx = text.find("\nADD_EXECUTABLE(")
        if idx == -1:
            idx = text.find("\nadd_executable(")
        if idx == -1:
            print("Cannot find ADD_EXECUTABLE anchor in CMakeLists.txt; skipping.")
            return False
        header = text[:idx + 1]
    else:
        nl = text.find("\n", idx + len(anchor))
        header = text[:nl + 1] if nl != -1 else text[:idx + len(anchor)]

    target = "%s_pubsub" % base
    lines = []
    lines.append("")
    lines.append("# All generated .c files compiled into the single combined pubsub binary")
    lines.append("ADD_EXECUTABLE(%s" % target)
    for f in c_files:
        lines.append("               ${CMAKE_CURRENT_SOURCE_DIR}/%s" % f)
    for f in h_files:
        lines.append("               ${CMAKE_CURRENT_SOURCE_DIR}/%s" % f)
    lines.append(")")
    lines.append("")
    lines.append("TARGET_LINK_LIBRARIES(%s" % target)
    lines.append("        ${MICRO_C_LIBS}")
    lines.append("        ${XML_LIBS}")
    lines.append("        ${SSL_LIBS}")
    lines.append("        ${PLATFORM_LIBS}")
    lines.append(")")
    lines.append("")

    with open(cmake_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(header + "\n".join(lines))

    print("CMakeLists.txt: target=%s, %d .c + %d .h files" % (target, len(c_files), len(h_files)))
    return True


def update_vcxproj(vcxproj_path, abs_outdir, c_files, h_files):
    text = open(vcxproj_path, "r", encoding="utf-8").read()

    # Only touch vcxproj files that already reference files in outdir
    if abs_outdir.replace("\\", "/").lower() not in text.replace("\\", "/").lower():
        return False

    # Build replacement ItemGroup
    lines = ["  <ItemGroup>"]
    for f in c_files:
        lines.append('    <ClCompile Include="%s" />' % os.path.join(abs_outdir, f))
    for f in h_files:
        lines.append('    <ClInclude Include="%s" />' % os.path.join(abs_outdir, f))
    lines.append("  </ItemGroup>")
    new_group = "\n".join(lines)

    # Match the ItemGroup block containing ClCompile/ClInclude entries for outdir
    pattern = re.compile(
        r'  <ItemGroup>\s*\n(?:[ \t]*<Cl(?:Compile|Include)\s+Include="[^"]*"[^/]*/>[\r\n]+)+  </ItemGroup>',
        re.MULTILINE,
    )
    match = None
    for m in pattern.finditer(text):
        if abs_outdir.replace("\\", "/").lower() in m.group().replace("\\", "/").lower():
            match = m
            break

    if match is None:
        print("  vcxproj: no matching ItemGroup in %s" % os.path.basename(vcxproj_path))
        return False

    new_text = text[:match.start()] + new_group + text[match.end():]
    with open(vcxproj_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(new_text)

    print("  vcxproj updated: %s" % os.path.basename(vcxproj_path))
    return True


def _keep_source(filename, base):
    # Exclude rtiddsgen-generated pub/sub example stubs (have their own main())
    # Keep only the generate_pubsub_one.py versions named exactly <base>_publisher/subscriber.c
    for suffix in ("_publisher.c", "_subscriber.c"):
        if filename.endswith(suffix) and filename != base + suffix:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, help="Output directory containing generated files")
    parser.add_argument("--base",   required=True, help="Base filename stem (e.g. dds_system)")
    args = parser.parse_args()

    abs_outdir = os.path.abspath(args.outdir)
    cmake_path = os.path.join(abs_outdir, "CMakeLists.txt")

    c_files = sorted(f for f in os.listdir(abs_outdir) if f.endswith(".c")
                     and _keep_source(f, args.base))
    h_files = sorted(f for f in os.listdir(abs_outdir) if f.endswith(".h"))

    if not c_files:
        print("No .c files found in %s; skipping." % abs_outdir)
        return 0

    print("Sources found (%d .c, %d .h):" % (len(c_files), len(h_files)))
    for f in c_files:
        print("  + %s" % f)

    if os.path.isfile(cmake_path):
        update_cmakelists(cmake_path, args.base, c_files, h_files)
    else:
        print("No CMakeLists.txt found; skipping cmake update.")

    # Walk subdirectories for .vcxproj files generated by cmake
    vcxproj_count = 0
    skip_names = {"ZERO_CHECK.vcxproj", "ALL_BUILD.vcxproj"}
    for dirpath, dirnames, filenames in os.walk(abs_outdir):
        dirnames[:] = [d for d in dirnames if d != "CMakeFiles"]
        for fname in filenames:
            if not fname.endswith(".vcxproj") or fname in skip_names:
                continue
            if update_vcxproj(os.path.join(dirpath, fname), abs_outdir, c_files, h_files):
                vcxproj_count += 1

    if vcxproj_count == 0:
        print("No vcxproj files updated (run cmake configure first to generate them).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
