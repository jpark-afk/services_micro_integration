#!/usr/bin/env python3
"""Comment conversion blocks for DDS types unused by a deployment."""
import argparse
import re
import xml.etree.ElementTree as ET


def local_name(value):
    return value.rsplit("::", 1)[-1] if value else ""


def parse_xml(path):
    return ET.parse(path).getroot()


def find_domain(root, domain_ref):
    library_name, domain_name = domain_ref.split("::", 1)
    for library in root.findall("domain_library"):
        if library.get("name") != library_name:
            continue
        for domain in library.findall("domain"):
            if domain.get("name") == domain_name:
                return domain
    raise ValueError("domain_ref not found: " + domain_ref)


def deployed_participant(root, deployment_name):
    deployment = root.find(".//deployment[@name='%s']" % deployment_name)
    if deployment is None:
        raise ValueError("deployment not found: " + deployment_name)

    application_ref = deployment.find("./applications/application")
    if application_ref is None:
        raise ValueError("deployment has no application: " + deployment_name)
    application_name = local_name(application_ref.get("application_ref"))

    application = root.find("./application_library/application[@name='%s']" % application_name)
    if application is None:
        raise ValueError("application not found: " + application_name)
    participant_ref = application.find("./domain_participant")
    if participant_ref is None:
        raise ValueError("application has no domain_participant: " + application_name)

    participant_name = local_name(participant_ref.get("base_name"))
    participant = root.find("./domain_participant_library/domain_participant[@name='%s']" % participant_name)
    if participant is None:
        raise ValueError("participant not found: " + participant_name)
    return participant


def used_types(root, deployment_name):
    participant = deployed_participant(root, deployment_name)
    topic_names = {
        local_name(endpoint.get("topic_ref"))
        for endpoint in participant.findall(".//data_writer") + participant.findall(".//data_reader")
        if endpoint.get("topic_ref")
    }
    domain = find_domain(root, participant.get("domain_ref"))
    topic_to_register = {
        topic.get("name"): local_name(topic.get("register_type_ref"))
        for topic in domain.findall("topic")
        if topic.get("name") and topic.get("register_type_ref")
    }
    missing_topics = sorted(topic_names - topic_to_register.keys())
    if missing_topics:
        raise ValueError("topic registration not found: " + ", ".join(missing_topics))

    register_to_type = {
        registration.get("name"): local_name(registration.get("type_ref"))
        for registration in domain.findall("register_type")
        if registration.get("name") and registration.get("type_ref")
    }
    register_names = {topic_to_register[name] for name in topic_names}
    missing_registers = sorted(register_names - register_to_type.keys())
    if missing_registers:
        raise ValueError("registered type not found: " + ", ".join(missing_registers))
    return {register_to_type[name] for name in register_names}


def unused_types(root, deployment_name):
    types = root.find("types")
    if types is None:
        raise ValueError("types section not found")
    all_types = {
        struct.get("name")
        for struct in types.findall("struct")
        if struct.get("name")
    }
    return all_types - used_types(root, deployment_name)


BLOCK_MARKER = re.compile(r"^/\* /([^\r\n]+) \*/\r?\n", re.MULTILINE)


def comment_unused_blocks(text, unused):
    matches = list(BLOCK_MARKER.finditer(text))
    changes = []
    pieces = []
    previous_end = 0
    for index, match in enumerate(matches):
        type_name = match.group(1)
        if type_name not in unused:
            continue
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        if text[match.end():].startswith("/* ") or text[match.end():].startswith("/*\r\n"):
            continue
        pieces.append(text[previous_end:match.start()])
        block_lines = text[match.start():block_end].rstrip("\r\n").splitlines()
        commented_lines = ["/* /%s */" % type_name]
        commented_lines.extend("/* %s */" % line for line in block_lines[1:])
        pieces.append("\n".join(commented_lines) + "\n")
        previous_end = block_end
        changes.append(type_name)
    if not changes:
        return text, changes
    pieces.append(text[previous_end:])
    return "".join(pieces), changes


def patch_file(path, unused):
    with open(path, "r", encoding="utf-8", newline="") as input_file:
        text = input_file.read()
    patched, changes = comment_unused_blocks(text, unused)
    if changes:
        with open(path, "w", encoding="utf-8", newline="") as output_file:
            output_file.write(patched)
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-xml", required=True)
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--c", dest="c_path", required=True)
    parser.add_argument("--h", dest="h_path", required=True)
    args = parser.parse_args()

    try:
        root = parse_xml(args.system_xml)
        unused = unused_types(root, args.deployment)
        c_changes = patch_file(args.c_path, unused)
        h_changes = patch_file(args.h_path, unused)
    except (ET.ParseError, OSError, ValueError) as error:
        parser.error(str(error))

    print("Unused types: %s" % (", ".join(sorted(unused)) if unused else "none"))
    print("C blocks commented: %s" % (", ".join(c_changes) if c_changes else "none"))
    print("H blocks commented: %s" % (", ".join(h_changes) if h_changes else "none"))


if __name__ == "__main__":
    main()