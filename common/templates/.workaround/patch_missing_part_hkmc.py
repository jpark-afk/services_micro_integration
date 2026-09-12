#!/usr/bin/env python3
"""Patch a raw HKMC DDS System XML with the parts a fresh customer export
is missing, entirely from built-in templates (no reference XML needed):

- The root xsi:noNamespaceSchemaLocation, pointed at the local Micro install
  schema instead of the community.rti.com URL.
- Per qos_profile <domain_participant_qos> blocks (discovery peers, transport
  interface/IP, discovery_config, properties), built from templates with
  placeholder IP addresses derived from --source's own domain_participant
  order. The "owner" ECU (its own interface address) is the participant that
  writes the topic behind the profile; readers of that topic become the
  remote initial_peers.
- The <application_library>/<node_library>/<deployment_library> overlay,
  built from --source's own domain_participant_library entries, with a
  built-in AUTOSAR configuration template attached to --autosar-participant.
All placeholder values ("[UPDATE REQUIRED]" comments, IPs, interface name,
heap size, etc.) are meant to be reviewed/edited per target ECU.

Explicitly NOT touched (handled by other scripts in the pipeline):
- <member type="..."> primitive type names -> patch_arcgen_types.py.
- <domain_participant name="..."> separators are normalized from "::" to "_"
    so the generated overlay can keep the library::participant qualifier unambiguous.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

SCHEMA_LOCATION_ATTR = "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation"
OVERLAY_TAGS = ("application_library", "node_library", "deployment_library")

DEFAULT_RTIMEHOME = (
    r"C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738"
)
DEFAULT_MULTICAST_ADDRESS = "239.255.0.1"
DEFAULT_NETWORK_PREFIX = "192.168.56."
DEFAULT_START_HOST = 101
DEFAULT_INTERFACE_NAME = "eth0"
DEFAULT_NET_MASK = "255.255.255.0"


def parse(xml_path):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.parse(xml_path, parser=parser)


def schema_location(args):
    return args.schema_location or (args.rtimehome + r"\rtiddsmag\resource\schema\dds-xml_system_definitions.xsd")


def normalize_participant_names(root, changes):
    library = root.find("domain_participant_library")
    if library is None:
        raise ValueError("domain_participant_library not found")

    for participant in library.findall("domain_participant"):
        name = participant.get("name")
        if not name:
            raise ValueError("domain_participant without a name")
        normalized_name = name.replace("::", "_")
        if normalized_name != name:
            participant.set("name", normalized_name)
            changes.append("domain_participant '%s' name -> '%s'" % (name, normalized_name))


def patch_schema_location(source_root, new_value, changes):
    if source_root.get(SCHEMA_LOCATION_ATTR) != new_value:
        source_root.set(SCHEMA_LOCATION_ATTR, new_value)
        changes.append("root xsi:noNamespaceSchemaLocation")


def participant_entries(root):
    library = root.find("domain_participant_library")
    if library is None:
        raise ValueError("domain_participant_library not found")

    entries = []
    for participant in library.findall("domain_participant"):
        participant_name = participant.get("name")
        if not participant_name:
            raise ValueError("domain_participant without a name")
        entries.append(participant_name)
    if not entries:
        raise ValueError("no domain_participant entries found")
    return entries


def participant_ip_map(participants, network_prefix, start_host):
    return {
        name: network_prefix + str(start_host + index)
        for index, name in enumerate(participants)
    }


def qos_profile_usage(root):
    """Map qos_profile name -> {'writer': participant name, 'readers': [participant names]}."""
    usage = {}
    library = root.find("domain_participant_library")
    for participant in library.findall("domain_participant"):
        participant_name = participant.get("name")
        for publisher in participant.findall("publisher"):
            for writer in publisher.findall("data_writer"):
                qos = writer.find("datawriter_qos")
                base_name = qos.get("base_name") if qos is not None else None
                if not base_name:
                    continue
                entry = usage.setdefault(base_name.split("::")[-1], {"writer": None, "readers": []})
                entry["writer"] = participant_name
        for subscriber in participant.findall("subscriber"):
            for reader in subscriber.findall("data_reader"):
                qos = reader.find("datareader_qos")
                base_name = qos.get("base_name") if qos is not None else None
                if not base_name:
                    continue
                entry = usage.setdefault(base_name.split("::")[-1], {"writer": None, "readers": []})
                entry["readers"].append(participant_name)
    return usage


def participant_qos_references(root):
    """Map participant name -> participant QoS base_name from its endpoint QoS."""
    library = root.find("domain_participant_library")
    references = {}
    for participant in library.findall("domain_participant"):
        participant_name = participant.get("name")
        participant_qos = participant.find("domain_participant_qos")
        if participant_qos is not None and participant_qos.get("base_name"):
            references[participant_name] = participant_qos.get("base_name")
            continue

        writer_references = []
        reader_references = []
        for publisher in participant.findall("publisher"):
            for writer in publisher.findall("data_writer"):
                qos = writer.find("datawriter_qos")
                if qos is not None and qos.get("base_name"):
                    writer_references.append(qos.get("base_name"))
        for subscriber in participant.findall("subscriber"):
            for reader in subscriber.findall("data_reader"):
                qos = reader.find("datareader_qos")
                if qos is not None and qos.get("base_name"):
                    reader_references.append(qos.get("base_name"))

        endpoint_references = writer_references or reader_references
        if endpoint_references:
            references[participant_name] = endpoint_references[0]
    return references


def build_domain_participant_qos(own_address, peer_addresses, interface_name, net_mask, multicast_address):
    qos = ET.Element("domain_participant_qos")
    discovery = ET.SubElement(qos, "discovery")
    ET.SubElement(discovery, "accept_unknown_peers").text = "false"
    initial_peers = ET.SubElement(discovery, "initial_peers")
    initial_peers.append(ET.Comment(" [UPDATE REQUIRED] Set the multicast address for the target subnet. "))
    ET.SubElement(initial_peers, "element").text = multicast_address
    for peer_address in peer_addresses:
        initial_peers.append(ET.Comment(" [UPDATE REQUIRED] Set the remote peer/controller IP address. "))
        ET.SubElement(initial_peers, "element").text = peer_address
    enabled_transports = ET.SubElement(discovery, "enabled_transports")
    ET.SubElement(enabled_transports, "element").text = "udpv4"
    multicast_receive = ET.SubElement(discovery, "multicast_receive_addresses")
    ET.SubElement(multicast_receive, "element").text = "udpv4://" + multicast_address

    default_unicast = ET.SubElement(qos, "default_unicast")
    value = ET.SubElement(default_unicast, "value")
    element = ET.SubElement(value, "element")
    transports = ET.SubElement(element, "transports")
    ET.SubElement(transports, "element").text = "udpv4"

    transport_builtin = ET.SubElement(qos, "transport_builtin")
    ET.SubElement(transport_builtin, "mask").text = "UDPv4"
    udpv4 = ET.SubElement(transport_builtin, "udpv4")
    udpv4.append(ET.Comment(" [UPDATE REQUIRED] Set the target network interface name. "))
    ET.SubElement(udpv4, "ignore_loopback_interface").text = "1"
    interface_table = ET.SubElement(udpv4, "interface_table")
    interface_element = ET.SubElement(interface_table, "element")
    ET.SubElement(interface_element, "interface_name").text = interface_name
    interface_element.append(ET.Comment(" [UPDATE REQUIRED] Set the target ECU interface IP address. "))
    ET.SubElement(interface_element, "address").text = own_address
    interface_element.append(ET.Comment(" [UPDATE REQUIRED] Set the target subnet mask. "))
    ET.SubElement(interface_element, "net_mask").text = net_mask
    ET.SubElement(interface_element, "flags").text = (
        "UDP_INTERFACE_INTERFACE_UP_FLAG|UDP_INTERFACE_INTERFACE_MULTICAST_FLAG"
    )
    allow_interfaces_list = ET.SubElement(udpv4, "allow_interfaces_list")
    allow_interfaces_list.append(ET.Comment(" [UPDATE REQUIRED] Must match interface_table/interface_name. "))
    ET.SubElement(allow_interfaces_list, "element").text = interface_name
    ET.SubElement(udpv4, "disable_auto_interface_config").text = "true"

    discovery_config = ET.SubElement(qos, "discovery_config")
    ET.SubElement(discovery_config, "builtin_discovery_plugins").text = "SDP"
    ET.SubElement(discovery_config, "initial_participant_announcements").text = "5"
    max_period = ET.SubElement(discovery_config, "max_initial_participant_announcement_period")
    ET.SubElement(max_period, "sec").text = "1"
    ET.SubElement(max_period, "nanosec").text = "0"
    assert_period = ET.SubElement(discovery_config, "participant_liveliness_assert_period")
    ET.SubElement(assert_period, "sec").text = "10"
    ET.SubElement(assert_period, "nanosec").text = "0"
    lease_duration = ET.SubElement(discovery_config, "participant_liveliness_lease_duration")
    ET.SubElement(lease_duration, "sec").text = "30"
    ET.SubElement(lease_duration, "nanosec").text = "0"

    property_element = ET.SubElement(qos, "property")
    value = ET.SubElement(property_element, "value")
    element = ET.SubElement(value, "element")
    ET.SubElement(element, "name").text = "dds.micro.discovery.enable_participant_discovery_by_name"
    ET.SubElement(element, "value").text = "true"

    return qos


def patch_domain_participant_qos(source_root, ip_map, interface_name, net_mask, multicast_address, changes):
    usage = qos_profile_usage(source_root)
    fallback_owner = next(iter(ip_map))

    for qos_library in source_root.findall("qos_library"):
        for qos_profile in qos_library.findall("qos_profile"):
            name = qos_profile.get("name")
            if qos_profile.find("domain_participant_qos") is not None:
                continue

            profile_usage = usage.get(name, {})
            owner = profile_usage.get("writer") or fallback_owner
            peers = [
                participant_name for participant_name in dict.fromkeys(profile_usage.get("readers", []))
                if participant_name != owner
            ]

            qos_profile.insert(0, ET.Comment(" [UPDATE REQUIRED] Review all peer IPs, interface names, and transport settings for this ECU. "))
            qos_profile.insert(
                1,
                build_domain_participant_qos(
                    ip_map[owner],
                    [ip_map[peer] for peer in peers],
                    interface_name,
                    net_mask,
                    multicast_address,
                ),
            )
            changes.append("qos_profile '%s' domain_participant_qos" % name)


def local_name(value):
    return value.replace("::", "_").replace(" ", "_")


def build_autosar(heap_size, heap_name, mutex_resource_id, max_local_addr_id, send_local_addr_id):
    autosar = ET.Element("autosar")
    heap = ET.SubElement(autosar, "heap")
    element = ET.SubElement(heap, "element")
    element.append(ET.Comment(
        " [REQUIRED] Heap size/name must match MCU memory design; edit start_address if the platform requires an explicit address. "
    ))
    ET.SubElement(element, "size").text = str(heap_size)
    start_address = ET.SubElement(element, "start_address")
    start_address.text = " "
    element.append(ET.Comment(" Workaround#HAE "))
    ET.SubElement(element, "name").text = heap_name
    autosar.append(ET.Comment(" [REQUIRED] Set DDS-dedicated OS resource name allocated in AUTOSAR OS config. "))
    ET.SubElement(autosar, "mutex_resource_id").text = mutex_resource_id
    autosar.append(ET.Comment(" [REQUIRED] Set to the highest index used in TcpIp local_addr_id configuration. "))
    ET.SubElement(autosar, "max_local_addr_id").text = str(max_local_addr_id)
    autosar.append(ET.Comment(" [REQUIRED] Set unicast local_addr_id that DDS will use for send path. "))
    ET.SubElement(autosar, "send_local_addr_id").text = str(send_local_addr_id)
    return autosar


def build_overlay(source_root, participants, participant_qos_refs, autosar_participant, autosar,
                  deployment_library_name, scenario_name, application_library_name, node_library_name,
                  changes):
    if autosar_participant not in participants:
        raise ValueError("AUTOSAR participant is not in domain_participant_library: " + autosar_participant)

    participant_library = source_root.find("domain_participant_library")
    participant_library_name = participant_library.get("name", "")

    for tag in OVERLAY_TAGS:
        for element in list(source_root.findall(tag)):
            source_root.remove(element)

    application_library = ET.Element("application_library", {"name": application_library_name})
    node_library = ET.Element("node_library", {"name": node_library_name})
    deployment_library = ET.Element("deployment_library", {"name": deployment_library_name})
    scenario = ET.SubElement(deployment_library, "deployment_scenario", {"name": scenario_name})

    for participant_name in participants:
        identifier = local_name(participant_name)
        application_name = identifier + "_Application"
        node_name = identifier + "_Node"
        deployment_name = identifier + "_Deployment"

        application = ET.SubElement(
            application_library,
            "application",
            {"name": application_name, "isCert": "false"},
        )
        overlay_participant = ET.SubElement(
            application,
            "domain_participant",
            {
                "name": identifier,
                "base_name": participant_library_name + "::" + participant_name,
            },
        )
        qos_base_name = participant_qos_refs.get(participant_name)
        if qos_base_name:
            ET.SubElement(overlay_participant, "domain_participant_qos", {"base_name": qos_base_name})
            changes.append("participant '%s' domain_participant_qos -> '%s'" % (participant_name, qos_base_name))
        ET.SubElement(node_library, "node", {"name": node_name})

        deployment = ET.SubElement(scenario, "deployment", {"name": deployment_name})
        ET.SubElement(deployment, "node", {"node_ref": node_library_name + "::" + node_name})
        applications = ET.SubElement(deployment, "applications")
        ET.SubElement(
            applications,
            "application",
            {
                "name": application_name,
                "application_ref": application_library_name + "::" + application_name,
            },
        )
        if participant_name == autosar_participant:
            configuration = ET.SubElement(deployment, "configuration")
            configuration.append(autosar)

    source_root.append(ET.Comment(
        " [REQUIRED] Deployment overlay for dds_system.xml\n"
        "    MCU controller-specific configuration starts here.\n"
        "    This section must be reviewed and configured for each target MCU project. "
    ))
    source_root.append(application_library)
    source_root.append(node_library)
    source_root.append(deployment_library)


def patch(source_path, output_path, args):
    source_tree = parse(source_path)
    source_root = source_tree.getroot()
    changes = []
    normalize_participant_names(source_root, changes)
    participants = participant_entries(source_root)
    participant_qos_refs = participant_qos_references(source_root)

    ip_map = participant_ip_map(participants, args.network_prefix, args.start_host)

    patch_schema_location(source_root, schema_location(args), changes)
    # Disabled: do not populate discovery, default_unicast, transport_builtin,
    # discovery_config, property, or writer_resource_limits in customer XML.
    # patch_domain_participant_qos(
    #     source_root, ip_map, args.interface_name, args.net_mask, args.multicast_address, changes
    # )

    autosar = build_autosar(
        args.heap_size, args.heap_name, args.mutex_resource_id, args.max_local_addr_id, args.send_local_addr_id
    )
    build_overlay(
        source_root,
        participants,
        participant_qos_refs,
        args.autosar_participant.replace("::", "_"),
        autosar,
        args.deployment_library,
        args.scenario,
        args.application_library,
        args.node_library,
        changes,
    )
    changes.append("application_library/node_library/deployment_library overlay")

    print("Patched: %s" % ", ".join(changes), file=sys.stderr)

    ET.indent(source_tree, space="  ")
    # ElementTree always writes the declaration with single quotes; force double quotes to match reference style.
    with open(output_path, "w", encoding="utf-8", newline="") as output_file:
        output_file.write('<?xml version="1.0" encoding="utf-8"?>\n')
        output_file.write("<!-- [UPDATE REQUIRED] xsi:noNamespaceSchemaLocation below is machine-specific; point it at this machine's Connext Micro install. -->\n")
        source_tree.write(output_file, encoding="unicode")
    print("Saved: %s" % output_path, file=sys.stderr)
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="Original/raw DDS System XML to patch (e.g. CODA export)")
    parser.add_argument("--output", help="Output XML path; defaults to <source>_patch.xml")
    parser.add_argument("--in-place", action="store_true", help="Replace the source XML")
    parser.add_argument("--autosar-participant", default="PDIO_FL::Domain_6",
                         help="Participant whose deployment gets the AUTOSAR configuration")
    parser.add_argument("--rtimehome", default=DEFAULT_RTIMEHOME, help="Connext Micro install root, used to derive --schema-location")
    parser.add_argument("--schema-location", help="Override the full xsi:noNamespaceSchemaLocation value")
    parser.add_argument("--network-prefix", default=DEFAULT_NETWORK_PREFIX, help="IP prefix used for placeholder participant addresses")
    parser.add_argument("--start-host", type=int, default=DEFAULT_START_HOST, help="First host number used for placeholder participant addresses")
    parser.add_argument("--interface-name", default=DEFAULT_INTERFACE_NAME)
    parser.add_argument("--net-mask", default=DEFAULT_NET_MASK)
    parser.add_argument("--multicast-address", default=DEFAULT_MULTICAST_ADDRESS)
    parser.add_argument("--heap-size", type=int, default=65536)
    parser.add_argument("--heap-name", default="ConnextDdsHeap")
    parser.add_argument("--mutex-resource-id", default="OsResource_Dds")
    parser.add_argument("--max-local-addr-id", type=int, default=2)
    parser.add_argument("--send-local-addr-id", type=int, default=0)
    parser.add_argument("--deployment-library", default="MyDeploymentLib")
    parser.add_argument("--scenario", default="MyDeploymentScenario")
    parser.add_argument("--application-library", default="MyApplicationLib")
    parser.add_argument("--node-library", default="MyNodeLib")
    args = parser.parse_args()

    if args.in_place and args.output:
        parser.error("--in-place and --output cannot be used together")
    if not os.path.isfile(args.source):
        print("ERROR: source file not found: %s" % args.source, file=sys.stderr)
        return 1

    output_path = args.source if args.in_place else args.output
    if output_path is None:
        base, ext = os.path.splitext(args.source)
        output_path = base + "_patch" + ext

    try:
        patch(args.source, output_path, args)
    except (ET.ParseError, OSError, ValueError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

