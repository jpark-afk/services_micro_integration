#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""
Generic multi-DataWriter / multi-DataReader publisher.c / subscriber.c generator
for RTI Connext Micro "mag" test apps.

Why this exists: rtiddsgen's "-exampleTemplate mag/dpde|dpse" Velocity templates
only ever see the LAST top-level <struct> in the DDS System XML (verified by
inspecting rtiddsgen2.jar's ASTEmitter/MicroCSourceEmitter bytecode: the Velocity
context is built per IDL type, not per DDS entity). The participant/publisher/
subscriber/data_writer/data_reader graph is only understood by rtiddsmag, never
by rtiddsgen's example templates. So rtiddsgen physically cannot loop over "all
datawriters in the XML" - that data isn't available to it.

This script instead parses the DDS System XML directly and generates
<base>_publisher.c, <base>_subscriber.c and <base>Entities.h with one code path
per data_writer / data_reader declared in the XML, for ANY input XML (not tied
to a specific project). Run this AFTER rtiddsgen has produced the rest of the
scaffolding (Application.c/h, Support, Plugin, etc.), so it only overwrites the
two example app source files plus adds one small generated header.

Usage:
    python generate_pubsub.py --xml <dds_system.xml> --outdir <dir> --base <basename>
"""
import argparse
import sys
import xml.etree.ElementTree as ET

# DDS primitive type -> (C storage type, printf format, printf cast, demo-value expr)
TYPE_INFO = {
    "short": ("DDS_Short", "%d", "(int)", "(DDS_Short)i"),
    "unsigned short": ("DDS_UnsignedShort", "%u", "(unsigned int)", "(DDS_UnsignedShort)i"),
    "long": ("DDS_Long", "%d", "(int)", "(DDS_Long)i"),
    "unsigned long": ("DDS_UnsignedLong", "%u", "(unsigned int)", "(DDS_UnsignedLong)i"),
    "long long": ("DDS_LongLong", "%lld", "(long long)", "(DDS_LongLong)i"),
    "unsigned long long": ("DDS_UnsignedLongLong", "%llu", "(unsigned long long)", "(DDS_UnsignedLongLong)i"),
    "octet": ("DDS_Octet", "%u", "(unsigned int)", "(DDS_Octet)i"),
    "boolean": ("DDS_Boolean", "%d", "(int)", "(DDS_Boolean)(i % 2)"),
    "char": ("DDS_Char", "%c", "(char)", "(DDS_Char)('A' + (i % 26))"),
    "wchar": ("DDS_Wchar", "%d", "(int)", "(DDS_Wchar)('A' + (i % 26))"),
    "float": ("DDS_Float", "%f", "(double)", "(DDS_Float)i"),
    "double": ("DDS_Double", "%f", "(double)", "(DDS_Double)i"),
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
        self.name = name          # e.g. "TestApp_TopicA_DW"
        self.topic = topic        # e.g. "TopicA"
        self.dds_type = dds_type  # e.g. "TypeA"
        self.members = members    # list[Member]

    @property
    def alias(self):
        """A short, C-identifier-safe alias derived from the topic name."""
        return "".join(c if (c.isalnum() or c == "_") else "_" for c in self.topic)


def parse_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 1. All struct member definitions, keyed by struct name.
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

    # 2. register_type name -> actual struct type_ref, and topic name -> register_type name.
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

    # 3. First domain_participant found (this generator produces one publisher_main
    #    and one subscriber_main per run, matching the two-binary test app layout).
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


def build_print_line(prefix, sample_var, members):
    """Build a single printf(...) statement summarizing all supported members."""
    parts_fmt = []
    parts_args = []
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


def build_set_sample_lines(sample_var, members):
    lines = []
    for m in members:
        if not m.supported:
            lines.append("    /* field '%s' (type '%s') not auto-populated by generator */" % (m.name, m.dds_type))
            continue
        if m.is_string:
            bound = m.string_max_length or "255"
            lines.append('    snprintf(%s->%s, sizeof(%s->%s), "msg-%%d", (int)i);' % (
                sample_var, m.name, sample_var, m.name))
        else:
            _, _, _, demo = TYPE_INFO[m.dds_type]
            lines.append("    %s->%s = %s;" % (sample_var, m.name, demo.replace("i", "i")))
    return "\n".join(lines)


def generate_entities_header(base, participant_name, writers, readers):
    guard = "%s_ENTITIES_H" % base.upper()
    lines = []
    lines.append("/* AUTO-GENERATED by templates/mag/generate_pubsub.py - DO NOT EDIT BY HAND */")
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


def generate_publisher_c(base, writers):
    out = []
    out.append("/* AUTO-GENERATED by templates/mag/generate_pubsub.py - DO NOT EDIT BY HAND */")
    out.append("")
    out.append('#include "rti_me_c.h"')
    out.append("")
    out.append("#include <stdio.h>")
    out.append("#include <stdlib.h>")
    out.append("#include <string.h>")
    out.append("")
    out.append('#include "wh_sm/wh_sm_history.h"')
    out.append('#include "rh_sm/rh_sm_history.h"')
    out.append("")
    out.append('#include "%s.h"' % base)
    out.append('#include "%sSupport.h"' % base)
    out.append('#include "%sPlugin.h"' % base)
    out.append("")
    out.append('#include "%sApplication.h"' % base)
    out.append('#include "%sEntities.h"' % base)
    out.append("")
    out.append("static DDS_Long g_publication_match_count = 0;")
    out.append("")
    out.append("static void")
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
    out.append("static int")
    out.append("publisher_main_w_args(DDS_Long sleep_time, DDS_Long count)")
    out.append("{")
    out.append("    DDS_ReturnCode_t retcode;")
    out.append("    struct Application *application = NULL;")
    out.append("    DDS_Long i;")
    out.append("    struct DDS_DataWriterListener dw_listener = DDS_DataWriterListener_INITIALIZER;")
    out.append("    int ret_value = -1;")
    out.append("")
    for w in writers:
        out.append("    DDS_DataWriter *%s_writer;" % w.alias)
        out.append("    %sDataWriter *%s_hw_writer;" % (w.dds_type, w.alias))
        out.append("    %s *%s_sample = NULL;" % (w.dds_type, w.alias))
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
    out.append("    #ifdef RTI_CERT")
    out.append("    #ifdef RTI_VXWORKS")
    out.append("    memAllocDisable();")
    out.append("    #endif")
    out.append("    #endif")
    out.append("")
    out.append("    for (i = 0; (application->count <= 0) || (i < application->count); ++i)")
    out.append("    {")
    out.append("        if (g_publication_match_count <= 0)")
    out.append("        {")
    out.append('            printf("No matched subscriber yet; waiting...\\n");')
    out.append("            OSAPI_Thread_sleep((RTI_UINT32)application->sleep_time);")
    out.append("            continue;")
    out.append("        }")
    out.append("")
    for w in writers:
        out.append(build_set_sample_lines("%s_sample" % w.alias, w.members))
        out.append("        retcode = %sDataWriter_write(%s_hw_writer, %s_sample, &DDS_HANDLE_NIL);" % (
            w.dds_type, w.alias, w.alias))
        out.append("        if (retcode != DDS_RETCODE_OK)")
        out.append("        {")
        out.append('            printf("Failed to write %s sample\\n");' % w.topic)
        out.append("        }")
        out.append("        else")
        out.append("        {")
        out.append("            %s" % build_print_line("Sent %s sample" % w.topic, "%s_sample" % w.alias, w.members))
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
    out.append("    return ret_value;")
    out.append("}")
    out.append("")
    out.append("#if !(defined(RTI_VXWORKS) && !defined(__RTP__))")
    out.append("int")
    out.append("main(int argc, char **argv)")
    out.append("{")
    out.append("    DDS_Long i = 0;")
    out.append("    DDS_Long sleep_time = 1000;")
    out.append("    DDS_Long count = 0;")
    out.append("    const char *peers = NULL;")
    out.append("")
    out.append("    for (i = 1; i < argc; ++i)")
    out.append("    {")
    out.append('        if (!strcmp(argv[i], "-sleep"))')
    out.append("        {")
    out.append("            ++i;")
    out.append("            if (i == argc)")
    out.append("            {")
    out.append('                printf("-sleep_time <sleep_time>\\n");')
    out.append("                return -1;")
    out.append("            }")
    out.append("            sleep_time = (DDS_Long)strtol(argv[i], NULL, 0);")
    out.append("        }")
    out.append('        else if (!strcmp(argv[i], "-count"))')
    out.append("        {")
    out.append("            ++i;")
    out.append("            if (i == argc)")
    out.append("            {")
    out.append('                printf("-count <count>\\n");')
    out.append("                return -1;")
    out.append("            }")
    out.append("            count = (DDS_Long)strtol(argv[i], NULL, 0);")
    out.append("        }")
    out.append('        else if (!strcmp(argv[i], "-peers"))')
    out.append("        {")
    out.append("            ++i;")
    out.append("            if (i == argc)")
    out.append("            {")
    out.append('                printf("-peers <peer_list>\\n");')
    out.append("                return -1;")
    out.append("            }")
    out.append("            peers = argv[i];")
    out.append("        }")
    out.append('        else if (!strcmp(argv[i], "-h"))')
    out.append("        {")
    out.append("            Application_help(argv[0]);")
    out.append("            return 0;")
    out.append("        }")
    out.append("        else")
    out.append("        {")
    out.append('            printf("unknown option: %s\\n", argv[i]);')
    out.append("            return -1;")
    out.append("        }")
    out.append("    }")
    out.append("")
    out.append("    (void)peers;")
    out.append("    return publisher_main_w_args(sleep_time, count);")
    out.append("}")
    out.append("#elif defined(RTI_VXWORKS)")
    out.append("int")
    out.append("publisher_main(void)")
    out.append("{")
    out.append("    DDS_Long sleep_time = 1000;")
    out.append("    DDS_Long count = 0;")
    out.append("")
    out.append("    return publisher_main_w_args(sleep_time, count);")
    out.append("}")
    out.append("#endif")
    out.append("")
    return "\n".join(out)


def generate_subscriber_c(base, readers):
    out = []
    out.append("/* AUTO-GENERATED by templates/mag/generate_pubsub.py - DO NOT EDIT BY HAND */")
    out.append("")
    out.append('#include "rti_me_c.h"')
    out.append("")
    out.append("#include <stdio.h>")
    out.append("#include <stdlib.h>")
    out.append("#include <string.h>")
    out.append("")
    out.append('#include "wh_sm/wh_sm_history.h"')
    out.append('#include "rh_sm/rh_sm_history.h"')
    out.append("")
    out.append('#include "%s.h"' % base)
    out.append('#include "%sSupport.h"' % base)
    out.append('#include "%sPlugin.h"' % base)
    out.append("")
    out.append('#include "%sApplication.h"' % base)
    out.append('#include "%sEntities.h"' % base)
    out.append("")
    out.append("static void")
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
        out.append("static void")
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
        out.append("            %s" % build_print_line("Received %s sample" % r.topic, "sample", r.members))
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
    out.append("static int")
    out.append("subscriber_main_w_args(DDS_Long sleep_time, DDS_Long count)")
    out.append("{")
    out.append("    DDS_ReturnCode_t retcode;")
    out.append("    struct Application *application = NULL;")
    out.append("    struct DDS_DataReaderListener dr_listener = DDS_DataReaderListener_INITIALIZER;")
    out.append("    int ret_value = -1;")
    out.append("    DDS_Long i;")
    for r in readers:
        out.append("    DDS_DataReader *%s_reader;" % r.alias)
        out.append("    DDS_Long %s_samples = 0;" % r.alias)
    out.append("")
    out.append("    application = Application_create(APP_PARTICIPANT_NAME, sleep_time, count);")
    out.append("    if (application == NULL)")
    out.append("    {")
    out.append('        printf("failed Application create\\n");')
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
    out.append('        printf("Subscriber sleeping for %d msec...\\n", application->sleep_time);')
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
    out.append("    #endif")
    out.append("")
    if readers:
        total_expr = " + ".join("%s_samples" % r.alias for r in readers)
        print_args = ", ".join("%s_samples" % r.alias for r in readers)
        print_fmt = " ".join("%s=%%d" % r.alias for r in readers)
        out.append("    if (ret_value == 0)")
        out.append("    {")
        out.append('        printf("Samples received: %s\\n", %s);' % (print_fmt, print_args))
        out.append("        if ((%s) == 0)" % total_expr)
        out.append("        {")
        out.append("            return -1;")
        out.append("        }")
        out.append("    }")
        out.append("")
    out.append("    return ret_value;")
    out.append("}")
    out.append("")
    out.append("#if !(defined(RTI_VXWORKS) && !defined(__RTP__))")
    out.append("int")
    out.append("main(int argc, char **argv)")
    out.append("{")
    out.append("    DDS_Long i = 0;")
    out.append("    DDS_Long sleep_time = 1000;")
    out.append("    DDS_Long count = 0;")
    out.append("    const char *peers = NULL;")
    out.append("")
    out.append("    for (i = 1; i < argc; ++i)")
    out.append("    {")
    out.append('        if (!strcmp(argv[i], "-sleep"))')
    out.append("        {")
    out.append("            ++i;")
    out.append("            if (i == argc)")
    out.append("            {")
    out.append('                printf("-sleep_time <sleep_time>\\n");')
    out.append("                return -1;")
    out.append("            }")
    out.append("            sleep_time = (DDS_Long)strtol(argv[i], NULL, 0);")
    out.append("        }")
    out.append('        else if (!strcmp(argv[i], "-count"))')
    out.append("        {")
    out.append("            ++i;")
    out.append("            if (i == argc)")
    out.append("            {")
    out.append('                printf("-count <count>\\n");')
    out.append("                return -1;")
    out.append("            }")
    out.append("            count = (DDS_Long)strtol(argv[i], NULL, 0);")
    out.append("        }")
    out.append('        else if (!strcmp(argv[i], "-peers"))')
    out.append("        {")
    out.append("            ++i;")
    out.append("            if (i == argc)")
    out.append("            {")
    out.append('                printf("-peers <peer_list>\\n");')
    out.append("                return -1;")
    out.append("            }")
    out.append("            peers = argv[i];")
    out.append("        }")
    out.append('        else if (!strcmp(argv[i], "-h"))')
    out.append("        {")
    out.append("            Application_help(argv[0]);")
    out.append("            return 0;")
    out.append("        }")
    out.append("        else")
    out.append("        {")
    out.append('            printf("unknown option: %s\\n", argv[i]);')
    out.append("            return -1;")
    out.append("        }")
    out.append("    }")
    out.append("")
    out.append("    (void)peers;")
    out.append("    return subscriber_main_w_args(sleep_time, count);")
    out.append("}")
    out.append("#elif defined(RTI_VXWORKS)")
    out.append("int")
    out.append("subscriber_main(void)")
    out.append("{")
    out.append("    DDS_Long sleep_time = 1000;")
    out.append("    DDS_Long count = 0;")
    out.append("")
    out.append("    return subscriber_main_w_args(sleep_time, count);")
    out.append("}")
    out.append("#endif")
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", required=True, help="Path to the DDS System XML file")
    parser.add_argument("--outdir", required=True, help="rtiddsgen output directory")
    parser.add_argument("--base", required=True, help="Base filename (e.g. testapp_system)")
    args = parser.parse_args()

    participant_name, writers, readers = parse_xml(args.xml)

    if not writers and not readers:
        print("No data_writer/data_reader entities found in %s; leaving rtiddsgen output as-is." % args.xml)
        return 0

    print("Participant: %s" % participant_name)
    print("DataWriters: %s" % ", ".join("%s(%s)" % (w.name, w.dds_type) for w in writers))
    print("DataReaders: %s" % ", ".join("%s(%s)" % (r.name, r.dds_type) for r in readers))

    import os
    entities_path = os.path.join(args.outdir, "%sEntities.h" % args.base)
    publisher_path = os.path.join(args.outdir, "%s_publisher.c" % args.base)
    subscriber_path = os.path.join(args.outdir, "%s_subscriber.c" % args.base)

    with open(entities_path, "w", newline="\n") as f:
        f.write(generate_entities_header(args.base, participant_name, writers, readers))
    with open(publisher_path, "w", newline="\n") as f:
        f.write(generate_publisher_c(args.base, writers))
    with open(subscriber_path, "w", newline="\n") as f:
        f.write(generate_subscriber_c(args.base, readers))

    print("Wrote %s" % entities_path)
    print("Wrote %s" % publisher_path)
    print("Wrote %s" % subscriber_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
