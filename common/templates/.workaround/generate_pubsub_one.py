#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""
Combined single-binary pubsub generator for RTI Connext Micro "mag" apps.

Unlike generate_pubsub.py (which produces separate publisher / subscriber
binaries each with their own main), this script generates a single binary
that publishes and subscribes simultaneously:

  <base>_publisher.c   - publication-matched callback only (no main)
  <base>_subscriber.c  - data-available callbacks only (no main)
  <base>_main.c        - <base>_pubsub() merging all writers + readers,
                         called by <base>_main() with sleep=1000, count=0

CMakeLists.txt in --outdir is patched to add a <base>_pubsub target.

Usage:
    python generate_pubsub_one.py --xml <dds_system.xml> --outdir <dir> --base <basename>
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

# DDS primitive type -> (C storage type, printf format, printf cast, demo-value expr)
TYPE_INFO = {
    "short":                ("DDS_Short",          "%d",   "(int)",               "(DDS_Short)i"),
    "unsigned short":       ("DDS_UnsignedShort",  "%u",   "(unsigned int)",      "(DDS_UnsignedShort)i"),
    "long":                 ("DDS_Long",           "%d",   "(int)",               "(DDS_Long)i"),
    "unsigned long":        ("DDS_UnsignedLong",   "%u",   "(unsigned int)",      "(DDS_UnsignedLong)i"),
    "long long":            ("DDS_LongLong",       "%lld", "(long long)",         "(DDS_LongLong)i"),
    "unsigned long long":   ("DDS_UnsignedLongLong","%llu","(unsigned long long)","(DDS_UnsignedLongLong)i"),
    "octet":                ("DDS_Octet",          "%u",   "(unsigned int)",      "(DDS_Octet)i"),
    "boolean":              ("DDS_Boolean",        "%d",   "(int)",               "(DDS_Boolean)(i % 2)"),
    "char":                 ("DDS_Char",           "%c",   "(char)",              "(DDS_Char)('A' + (i % 26))"),
    "wchar":                ("DDS_Wchar",          "%d",   "(int)",               "(DDS_Wchar)('A' + (i % 26))"),
    "float":                ("DDS_Float",          "%f",   "(double)",            "(DDS_Float)i"),
    "double":               ("DDS_Double",         "%f",   "(double)",            "(DDS_Double)i"),
}


class Member:
    def __init__(self, name, dds_type, is_string, string_max_length):
        self.name = name
        self.dds_type = dds_type
        self.is_string = is_string
        self.string_max_length = string_max_length

    @property
    def supported(self):
        return self.is_string or self.dds_type in TYPE_INFO


class Endpoint:
    def __init__(self, name, topic, dds_type, members):
        self.name = name
        self.topic = topic
        self.dds_type = dds_type
        self.members = members

    @property
    def alias(self):
        return "".join(c if (c.isalnum() or c == "_") else "_" for c in self.topic)


def parse_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    struct_members = {}
    for struct_el in root.findall("./types/struct"):
        members = []
        for member_el in struct_el.findall("member"):
            name = member_el.get("name")
            dds_type = member_el.get("type", "")
            is_string = dds_type == "string"
            string_max_length = member_el.get("stringMaxLength")
            members.append(Member(name, dds_type, is_string, string_max_length))
        struct_members[struct_el.get("name")] = members

    register_type_to_struct = {}
    topic_to_register_type = {}
    for domain_el in root.findall("./domain_library/domain"):
        for reg_el in domain_el.findall("register_type"):
            register_type_to_struct[reg_el.get("name")] = reg_el.get("type_ref")
        for topic_el in domain_el.findall("topic"):
            topic_to_register_type[topic_el.get("name")] = topic_el.get("register_type_ref")

    def resolve_topic_type(topic_ref):
        simple_name = topic_ref.split("::")[-1]
        reg_name = topic_to_register_type.get(simple_name, simple_name)
        return register_type_to_struct.get(reg_name, reg_name)

    participant_lib = root.find("./domain_participant_library")
    if participant_lib is None:
        raise SystemExit("No <domain_participant_library> found in %s" % xml_path)
    participant_el = participant_lib.find("domain_participant")
    if participant_el is None:
        raise SystemExit("No <domain_participant> found in %s" % xml_path)

    participant_qualified_name = "%s::%s" % (participant_lib.get("name"), participant_el.get("name"))

    writers = []
    for pub_el in participant_el.findall("publisher"):
        for dw_el in pub_el.findall("data_writer"):
            topic_ref = dw_el.get("topic_ref")
            dds_type = resolve_topic_type(topic_ref)
            full_name = "%s::%s" % (pub_el.get("name"), dw_el.get("name"))
            writers.append(Endpoint(full_name, topic_ref, dds_type, struct_members.get(dds_type, [])))

    readers = []
    for sub_el in participant_el.findall("subscriber"):
        for dr_el in sub_el.findall("data_reader"):
            topic_ref = dr_el.get("topic_ref")
            dds_type = resolve_topic_type(topic_ref)
            full_name = "%s::%s" % (sub_el.get("name"), dr_el.get("name"))
            readers.append(Endpoint(full_name, topic_ref, dds_type, struct_members.get(dds_type, [])))

    return participant_qualified_name, writers, readers


def _build_print_line(prefix, sample_var, members):
    parts_fmt, parts_args = [], []
    for m in members:
        if not m.supported:
            continue
        if m.is_string:
            parts_fmt.append("%s=%%s" % m.name)
            parts_args.append("%s->%s" % (sample_var, m.name))
        else:
            _, fmt, cast, _ = TYPE_INFO[m.dds_type]
            parts_fmt.append("%s=%s" % (m.name, fmt))
            parts_args.append("%s(%s->%s)" % (cast, sample_var, m.name))
    if not parts_fmt:
        return 'printf("%s (no printable members)\\n");' % prefix
    fmt_str = prefix + ": " + " ".join(parts_fmt) + "\\n"
    if parts_args:
        return 'printf("%s", %s);' % (fmt_str, ", ".join(parts_args))
    return 'printf("%s");' % fmt_str


def _build_set_sample_lines(sample_var, members):
    lines = []
    for m in members:
        if not m.supported:
            lines.append("    /* field '%s' (type '%s') not auto-populated */" % (m.name, m.dds_type))
            continue
        if m.is_string:
            lines.append('    snprintf(%s->%s, sizeof(%s->%s), "msg-%%d", (int)i);' % (
                sample_var, m.name, sample_var, m.name))
        else:
            _, _, _, demo = TYPE_INFO[m.dds_type]
            lines.append("    %s->%s = %s;" % (sample_var, m.name, demo))
    return "\n".join(lines)


def _file_header(base, xml_base):
    # xml_base: stem of rtiddsgen-generated headers (may differ from base when XML was patched)
    return [
        "/* AUTO-GENERATED by templates/mag/generate_pubsub_one.py - DO NOT EDIT BY HAND */",
        "",
        '#include "rti_me_c.h"',
        "",
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <string.h>",
        "",
        '#include "wh_sm/wh_sm_history.h"',
        '#include "rh_sm/rh_sm_history.h"',
        "",
        '#include "%s.h"' % xml_base,
        '#include "%sSupport.h"' % xml_base,
        '#include "%sPlugin.h"' % xml_base,
        "",
        '#include "%sApplication.h"' % xml_base,
        '#include "%sEntities.h"' % base,
        "",
    ]


def generate_entities_header(base, participant_name, writers, readers):
    guard = "%s_ENTITIES_H" % base.upper()
    lines = []
    lines.append("/* AUTO-GENERATED by templates/mag/generate_pubsub_one.py - DO NOT EDIT BY HAND */")
    lines.append("#ifndef %s" % guard)
    lines.append("#define %s" % guard)
    lines.append("")
    lines.append('#define APP_PARTICIPANT_NAME "%s"' % participant_name)
    lines.append("")
    for w in writers:
        lines.append('#define PUB_%s_DATAWRITER_NAME "%s"' % (w.alias.upper(), w.name))
    lines.append("")
    for r in readers:
        lines.append('#define SUB_%s_DATAREADER_NAME "%s"' % (r.alias.upper(), r.name))
    lines.append("")
    lines.append("#endif")
    lines.append("")
    return "\n".join(lines)


def generate_publisher_c(base, xml_base, writers):
    """Callback file only - no main, no publisher_main_w_args."""
    out = _file_header(base, xml_base)
    out.append("DDS_Long g_publication_match_count = 0;")
    out.append("")
    out.append("void")
    out.append("Publisher_on_publication_matched(")
    out.append("    void *listener_data,")
    out.append("    DDS_DataWriter *writer,")
    out.append("    const struct DDS_PublicationMatchedStatus *status)")
    out.append("{")
    out.append("    (void)listener_data;")
    out.append("    (void)writer;")
    out.append("")
    out.append("    if (status->current_count_change > 0)")
    out.append("    {")
    out.append("        g_publication_match_count = status->current_count;")
    out.append('        printf("Matched a subscriber\\n");')
    out.append("    }")
    out.append("    else if (status->current_count_change < 0)")
    out.append("    {")
    out.append("        g_publication_match_count = status->current_count;")
    out.append("        if (g_publication_match_count < 0)")
    out.append("        {")
    out.append("            g_publication_match_count = 0;")
    out.append("        }")
    out.append('        printf("Unmatched a subscriber\\n");')
    out.append("    }")
    out.append("}")
    out.append("")
    return "\n".join(out)


def generate_subscriber_c(base, xml_base, readers):
    """Callback files only - no main, no subscriber_main_w_args."""
    out = _file_header(base, xml_base)
    out.append("void")
    out.append("Subscriber_on_subscription_matched(")
    out.append("    void *listener_data,")
    out.append("    DDS_DataReader *reader,")
    out.append("    const struct DDS_SubscriptionMatchedStatus *status)")
    out.append("{")
    out.append("    (void)listener_data;")
    out.append("    (void)reader;")
    out.append("")
    out.append("    if (status->current_count_change > 0)")
    out.append("    {")
    out.append('        printf("Matched a publisher\\n");')
    out.append("    }")
    out.append("    else if (status->current_count_change < 0)")
    out.append("    {")
    out.append('        printf("Unmatched a publisher\\n");')
    out.append("    }")
    out.append("}")
    out.append("")
    for r in readers:
        out.append("void")
        out.append("%s_on_data_available(" % r.alias)
        out.append("    void *listener_data,")
        out.append("    DDS_DataReader *reader)")
        out.append("{")
        out.append("    %sDataReader *hw_reader = %sDataReader_narrow(reader);" % (r.dds_type, r.dds_type))
        out.append("    DDS_ReturnCode_t retcode;")
        out.append("    struct DDS_SampleInfo *sample_info = NULL;")
        out.append("    %s *sample = NULL;" % r.dds_type)
        out.append("    struct DDS_SampleInfoSeq info_seq = DDS_SEQUENCE_INITIALIZER;")
        out.append("    struct %sSeq sample_seq = DDS_SEQUENCE_INITIALIZER;" % r.dds_type)
        out.append("    DDS_Long i;")
        out.append("    DDS_Long *total_samples = (DDS_Long*) listener_data;")
        out.append("")
        out.append("    retcode = %sDataReader_take(" % r.dds_type)
        out.append("        hw_reader, &sample_seq, &info_seq,")
        out.append("        DDS_LENGTH_UNLIMITED, DDS_ANY_SAMPLE_STATE, DDS_ANY_VIEW_STATE, DDS_ANY_INSTANCE_STATE);")
        out.append("    if (retcode != DDS_RETCODE_OK)")
        out.append("    {")
        out.append('        printf("%s: failed to take data, retcode(%%d)\\n", retcode);' % r.topic)
        out.append("        goto done;")
        out.append("    }")
        out.append("")
        out.append("    for (i = 0; i < %sSeq_get_length(&sample_seq); ++i)" % r.dds_type)
        out.append("    {")
        out.append("        sample_info = DDS_SampleInfoSeq_get_reference(&info_seq, i);")
        out.append("        if (sample_info->valid_data)")
        out.append("        {")
        out.append("            sample = %sSeq_get_reference(&sample_seq, i);" % r.dds_type)
        out.append("            %s" % _build_print_line("Received %s sample" % r.topic, "sample", r.members))
        out.append("            *total_samples += 1;")
        out.append("        }")
        out.append("        else")
        out.append("        {")
        out.append('            printf("%s: sample received, INVALID DATA\\n");' % r.topic)
        out.append("        }")
        out.append("    }")
        out.append("")
        out.append("    %sDataReader_return_loan(hw_reader, &sample_seq, &info_seq);" % r.dds_type)
        out.append("")
        out.append("    done:")
        out.append("    #ifndef RTI_CERT")
        out.append("    %sSeq_finalize(&sample_seq);" % r.dds_type)
        out.append("    DDS_SampleInfoSeq_finalize(&info_seq);")
        out.append("    #else")
        out.append("    return;")
        out.append("    #endif")
        out.append("}")
        out.append("")
    return "\n".join(out)


def generate_main_c(base, xml_base, writers, readers):
    """Combined <base>_pubsub() + <base>_main() entry point."""
    out = _file_header(base, xml_base)
    if writers:
        out.append("extern DDS_Long g_publication_match_count;")
        out.append("extern void Publisher_on_publication_matched(void *, DDS_DataWriter *,")
        out.append("    const struct DDS_PublicationMatchedStatus *);")
        out.append("")
    if readers:
        out.append("extern void Subscriber_on_subscription_matched(void *, DDS_DataReader *,")
        out.append("    const struct DDS_SubscriptionMatchedStatus *);")
        for r in readers:
            out.append("extern void %s_on_data_available(void *, DDS_DataReader *);" % r.alias)
        out.append("")
    out.append("static int")
    out.append("%s_pubsub(DDS_Long sleep_time, DDS_Long count)" % base)
    out.append("{")
    out.append("    DDS_ReturnCode_t retcode;")
    out.append("    struct Application *application = NULL;")
    if writers:
        out.append("    struct DDS_DataWriterListener dw_listener = DDS_DataWriterListener_INITIALIZER;")
    if readers:
        out.append("    struct DDS_DataReaderListener dr_listener = DDS_DataReaderListener_INITIALIZER;")
    out.append("    int ret_value = -1;")
    out.append("    DDS_Long i;")
    for w in writers:
        out.append("    DDS_DataWriter *%s_writer;" % w.alias)
        out.append("    %sDataWriter *%s_hw_writer;" % (w.dds_type, w.alias))
        out.append("    %s *%s_sample = NULL;" % (w.dds_type, w.alias))
    for r in readers:
        out.append("    DDS_DataReader *%s_reader;" % r.alias)
        out.append("    DDS_Long %s_samples = 0;" % r.alias)
    out.append("")
    for w in writers:
        out.append("    %s_sample = %sTypeSupport_create_data();" % (w.alias, w.dds_type))
        out.append("    if (%s_sample == NULL)" % w.alias)
        out.append("    {")
        out.append('        printf("failed %sTypeSupport_create_data\\n");' % w.dds_type)
        out.append("        goto done;")
        out.append("    }")
        out.append("")
    out.append("    application = Application_create(APP_PARTICIPANT_NAME, sleep_time, count);")
    out.append("    if (application == NULL)")
    out.append("    {")
    out.append('        printf("failed Application create\\n");')
    out.append("        goto done;")
    out.append("    }")
    out.append("")
    for w in writers:
        out.append("    %s_writer = DDS_DomainParticipant_lookup_datawriter_by_name(" % w.alias)
        out.append("        application->participant,")
        out.append("        PUB_%s_DATAWRITER_NAME);" % w.alias.upper())
        out.append("    if (%s_writer == NULL)" % w.alias)
        out.append("    {")
        out.append('        printf("%s_writer == NULL\\n");' % w.alias)
        out.append("        goto done;")
        out.append("    }")
        out.append("")
    for r in readers:
        out.append("    %s_reader = DDS_DomainParticipant_lookup_datareader_by_name(" % r.alias)
        out.append("        application->participant,")
        out.append("        SUB_%s_DATAREADER_NAME);" % r.alias.upper())
        out.append("    if (%s_reader == NULL)" % r.alias)
        out.append("    {")
        out.append('        printf("%s_reader == NULL\\n");' % r.alias)
        out.append("        goto done;")
        out.append("    }")
        out.append("")
    if writers:
        out.append("    dw_listener.on_publication_matched = Publisher_on_publication_matched;")
        out.append("")
        for w in writers:
            out.append("    retcode = DDS_DataWriter_set_listener(")
            out.append("        %s_writer, &dw_listener, DDS_PUBLICATION_MATCHED_STATUS);" % w.alias)
            out.append("    if (retcode != DDS_RETCODE_OK)")
            out.append("    {")
            out.append('        printf("failed to set %s writer listener\\n");' % w.alias)
            out.append("        goto done;")
            out.append("    }")
            out.append("")
        for w in writers:
            out.append("    %s_hw_writer = %sDataWriter_narrow(%s_writer);" % (w.alias, w.dds_type, w.alias))
        out.append("")
    if readers:
        out.append("    dr_listener.on_subscription_matched = Subscriber_on_subscription_matched;")
        out.append("")
        for r in readers:
            out.append("    dr_listener.on_data_available = %s_on_data_available;" % r.alias)
            out.append("    dr_listener.as_listener.listener_data = &%s_samples;" % r.alias)
            out.append("    retcode = DDS_DataReader_set_listener(")
            out.append("        %s_reader, &dr_listener," % r.alias)
            out.append("        DDS_DATA_AVAILABLE_STATUS | DDS_SUBSCRIPTION_MATCHED_STATUS);")
            out.append("    if (retcode != DDS_RETCODE_OK)")
            out.append("    {")
            out.append('        printf("failed to set %s reader listener\\n");' % r.alias)
            out.append("        goto done;")
            out.append("    }")
            out.append("")
    out.append("    #ifdef RTI_CERT")
    out.append("    #ifdef RTI_VXWORKS")
    out.append("    memAllocDisable();")
    out.append("    #endif")
    out.append("    #endif")
    out.append("")
    out.append("    for (i = 0; (application->count <= 0) || (i < application->count); ++i)")
    out.append("    {")
    if writers:
        out.append("        if (g_publication_match_count <= 0)")
        out.append("        {")
        out.append('            printf("No matched subscriber yet; waiting...\\n");')
        out.append("            OSAPI_Thread_sleep((RTI_UINT32)application->sleep_time);")
        out.append("            continue;")
        out.append("        }")
        out.append("")
    for w in writers:
        out.append(_build_set_sample_lines("%s_sample" % w.alias, w.members))
        out.append("        retcode = %sDataWriter_write(%s_hw_writer, %s_sample, &DDS_HANDLE_NIL);" % (
            w.dds_type, w.alias, w.alias))
        out.append("        if (retcode != DDS_RETCODE_OK)")
        out.append("        {")
        out.append('            printf("Failed to write %s sample\\n");' % w.topic)
        out.append("        }")
        out.append("        else")
        out.append("        {")
        out.append("            %s" % _build_print_line(
            "Sent %s sample" % w.topic, "%s_sample" % w.alias, w.members))
        out.append("        }")
        out.append("")
    out.append("        OSAPI_Thread_sleep((RTI_UINT32)application->sleep_time);")
    out.append("    }")
    out.append("")
    out.append("    ret_value = 0;")
    out.append("")
    out.append("    done:")
    out.append("")
    out.append("    #ifndef RTI_CERT")
    out.append("    if (application != NULL)")
    out.append("    {")
    out.append("        Application_delete(application);")
    out.append("    }")
    out.append("")
    for w in writers:
        out.append("    if (%s_sample != NULL)" % w.alias)
        out.append("    {")
        out.append("        %sTypeSupport_delete_data(%s_sample);" % (w.dds_type, w.alias))
        out.append("    }")
        out.append("")
    out.append("    #endif")
    out.append("")
    if readers:
        print_fmt = " ".join("%s=%%d" % r.alias for r in readers)
        print_args = ", ".join("%s_samples" % r.alias for r in readers)
        out.append("    if (ret_value == 0)")
        out.append("    {")
        out.append('        printf("Samples received: %s\\n", %s);' % (print_fmt, print_args))
        out.append("    }")
        out.append("")
    out.append("    return ret_value;")
    out.append("}")
    out.append("")
    out.append("#if !(defined(RTI_VXWORKS) && !defined(__RTP__))")
    out.append("int")
    out.append("%s_main(int argc, char **argv)" % base)
    out.append("{")
    out.append("    (void)argc;")
    out.append("    (void)argv;")
    out.append("    return %s_pubsub(1000, 0);" % base)
    out.append("}")
    out.append("")
    out.append("int")
    out.append("main(int argc, char **argv)")
    out.append("{")
    out.append("    return %s_main(argc, argv);" % base)
    out.append("}")
    out.append("#elif defined(RTI_VXWORKS)")
    out.append("int")
    out.append("%s_main(void)" % base)
    out.append("{")
    out.append("    return %s_pubsub(1000, 0);" % base)
    out.append("}")
    out.append("#endif")
    out.append("")
    return "\n".join(out)


def patch_cmakelists_add_pubsub(base, outdir):
    """Inject a combined <base>_pubsub executable target into the generated CMakeLists.txt."""
    cmake_path = os.path.join(outdir, "CMakeLists.txt")
    if not os.path.isfile(cmake_path):
        return

    text = open(cmake_path, "r", encoding="utf-8").read()
    marker = "# BEGIN pubsub target"
    if marker in text:
        return

    pub_target = "%s_publisher" % base
    sub_target = "%s_subscriber" % base
    pubsub_target = "%s_pubsub" % base

    new_block = """
# BEGIN pubsub target
ADD_EXECUTABLE(%(pubsub)s
               ${CMAKE_CURRENT_SOURCE_DIR}/%(base)s_main.${SOURCE_EXTENSION}
               ${CMAKE_CURRENT_SOURCE_DIR}/%(base)s_publisher.${SOURCE_EXTENSION}
               ${CMAKE_CURRENT_SOURCE_DIR}/%(base)s_subscriber.${SOURCE_EXTENSION}
               ${CMAKE_CURRENT_SOURCE_DIR}/%(base)sApplication.${SOURCE_EXTENSION}
               ${CMAKE_CURRENT_SOURCE_DIR}/%(base)sApplication.h
               ${IDL_GEN_C} ${IDL_GEN_H} ${APP_GEN_C} ${APP_GEN_H})

TARGET_LINK_LIBRARIES(%(pubsub)s
        ${MICRO_C_LIBS}
        ${XML_LIBS}
        ${SSL_LIBS}
        ${PLATFORM_LIBS}
)
# END pubsub target
""" % {"pubsub": pubsub_target, "base": base}

    shim_marker = "# BEGIN isoc23 shim injection"
    idx = text.find(shim_marker)
    if idx != -1:
        text = text[:idx] + new_block + text[idx:]
    else:
        text = text + new_block

    # Add pubsub to the isoc23 shim target loop if present
    shim_pattern = "        %s\n        %s\n" % (pub_target, sub_target)
    if shim_pattern in text:
        text = text.replace(
            shim_pattern,
            "        %s\n        %s\n        %s\n" % (pub_target, sub_target, pubsub_target),
        )

    with open(cmake_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("Patched CMakeLists.txt: added %s target" % pubsub_target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml",    required=True, help="Path to the DDS System XML file")
    parser.add_argument("--outdir", required=True, help="rtiddsgen output directory")
    parser.add_argument("--base",   required=True, help="Base filename (e.g. dds_system)")
    args = parser.parse_args()

    # xml_base: stem of the XML fed to rtiddsgen - determines generated header filenames
    xml_base = os.path.splitext(os.path.basename(args.xml))[0]

    participant_name, writers, readers = parse_xml(args.xml)

    if not writers and not readers:
        print("No data_writer/data_reader entities found; leaving rtiddsgen output as-is.")
        return 0

    print("Participant: %s" % participant_name)
    print("xml_base=%s  base=%s" % (xml_base, args.base))
    print("DataWriters: %s" % ", ".join("%s(%s)" % (w.name, w.dds_type) for w in writers))
    print("DataReaders: %s" % ", ".join("%s(%s)" % (r.name, r.dds_type) for r in readers))

    entities_path   = os.path.join(args.outdir, "%sEntities.h"    % args.base)
    publisher_path  = os.path.join(args.outdir, "%s_publisher.c"  % args.base)
    subscriber_path = os.path.join(args.outdir, "%s_subscriber.c" % args.base)
    main_path       = os.path.join(args.outdir, "%s_main.c"       % args.base)

    with open(entities_path,   "w", newline="\n") as f:
        f.write(generate_entities_header(args.base, participant_name, writers, readers))
    with open(publisher_path,  "w", newline="\n") as f:
        f.write(generate_publisher_c(args.base, xml_base, writers))
    with open(subscriber_path, "w", newline="\n") as f:
        f.write(generate_subscriber_c(args.base, xml_base, readers))
    with open(main_path,       "w", newline="\n") as f:
        f.write(generate_main_c(args.base, xml_base, writers, readers))

    print("Wrote %s" % entities_path)
    print("Wrote %s" % publisher_path)
    print("Wrote %s" % subscriber_path)
    print("Wrote %s" % main_path)

    patch_cmakelists_add_pubsub(args.base, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
