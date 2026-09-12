# Architecture Guide

## About This Document

This document describes the **three-layer architecture of the DDS CDD** that the RTI Micro Application Generator (MAG) produces. MAG generates a complete CDD scaffold from a DDS-XML system definition; the architecture explained here applies to **any** MAG-generated CDD regardless of the specific topics, types, or participants defined in the XML.

To make the concepts concrete, code examples in this guide use the **ECU_SEAT_ZoneRR** participant generated for this repository (topics such as `ZcRR_SeatCmd` and `EcuSeat_Status`). These are illustrative — your generated code will contain different topic names, type names, and endpoint configurations depending on your DDS-XML input. The architectural patterns and layer responsibilities remain the same.

### When to Read This Guide

**After successful integration** (recommended):
- You want to understand the design decisions in depth
- You're modifying the generated implementation for advanced use cases
- You're explaining the system architecture to your team
- You need to debug complex integration issues

**Before integration** (optional):
- You're an architect evaluating the MAG-generated CDD approach
- You need to understand the design before proceeding
- You're planning your integration strategy

**Most users:** Read the [Integration Guide](../Integration%20kit/Integration%20guide.md) first for a step-by-step workflow, then come here for deeper technical understanding.

---

## Overview

The MAG-generated DDS CDD provides a layered architecture for integrating RTI Connext DDS Micro 4 into AUTOSAR Classic Platform systems. This guide describes the architectural patterns, component interactions, and design decisions that MAG applies to every generated CDD.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Application SW-C Layer                    │
│              (Your application or example ASWC)             │
└────────────────────────┬────────────────────────────────────┘
                         │ RTE Ports
┌────────────────────────▼────────────────────────────────────┐
│                    AUTOSAR RTE Layer                        │
└────────────────────────┬────────────────────────────────────┘
                         │ RTE Ports
┌────────────────────────▼────────────────────────────────────┐
│               DDS CDD SW-C Layer (MAG-generated)           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 1: AUTOSAR Template (DdsCdd.c)                │   │
│  │  - Runnables mapped to OS tasks                      │   │
│  │  - Thin wrapper calling adapter functions            │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  Layer 2: Adapter (dds_cdd_adapter.c/h)              │   │
│  │  - RTE to DDS type conversion                        │   │
│  │  - TcpIp integration                                 │   │
│  │  - Initialization state machine                      │   │
│  │  - AUTOSAR system property configuration             │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  Layer 3: DDS Implementation (dds_impl.c/h)          │   │
│  │  - DDS entity creation and management                │   │
│  │  - DataWriter/DataReader operations                  │   │
│  │  - QoS configuration                                 │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │ DDS API
┌─────────────────────────▼───────────────────────────────────┐
│              RTI Connext DDS Micro Layer                    │
│  - Domain Participant                                       │
│  - Topics, Publishers, Subscribers                          │
│  - DataWriters, DataReaders                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │ Network I/O
┌─────────────────────────▼───────────────────────────────────┐
│              AUTOSAR TcpIp (Eth Stack)                      │
└─────────────────────────────────────────────────────────────┘
```

## Three-Layer DDS CDD Architecture

### Layer 1: RTE Template Layer

**File**: `<participant>/autosar_gen/DdsCdd.c` (MAG-generated)

**Purpose**: AUTOSAR SW-C implementation that serves as the interface between the RTE and the DDS functionality.

**Generation**: MAG generates the runnable implementations that call into the adapter layer. The RTE generator separately creates the function signatures and contract-phase headers. You may need to complete `TODO` markers in the adapter layer, but the DdsCdd.c runnables are fully generated.

**Responsibilities**:
- Implement runnables with trigger conditions (configured in ARXML)
- Handle all RTE read/write operations (interacts with RTE ports)
- Pass RTE data structures as parameters to adapter layer
- Provide thin wrapper with minimal business logic

**Key Runnables (MAG-Generated)**:

MAG generates these runnables with calls to the corresponding adapter layer functions. The pattern is the same for every topic — only the topic and type names change:

```c
// Initialization runnable (triggered by InitEvent trigger condition)
FUNC(void, DdsCdd_CODE) DdsCddStart(void)
{
    DdsCdd_Adapter_Init();
}

// Timer runnable for DDS QoS maintenance (10ms periodic trigger condition)
FUNC(void, DdsCdd_CODE) DdsCddRun(void)
{
    DdsCdd_Adapter_Run();
}

// Data reception runnable (periodic trigger condition)
// Pattern: MAG generates one runnable per DDS topic the participant subscribes to
FUNC(void, DdsCdd_CODE) DdsCddRead_<TopicName>(void)
{
    <TopicType>_t rte_data;
    
    // Poll from DDS via adapter (adapter returns converted data)
    if (DdsCdd_Adapter_Poll_<TopicName>(&rte_data) == 0)
    {
        // Write received data to RTE port for application consumption
        Rte_Write_S_<TopicName>_<TopicType>_t(&rte_data);
    }
}

// Example from ECU_SEAT_ZoneRR: subscribing to ZcRR_SeatCmd
FUNC(void, DdsCdd_CODE) DdsCddRead_ZcRR_SeatCmd(void)
{
    SeatCommand_t rte_data;
    if (DdsCdd_Adapter_Poll_ZcRR_SeatCmd(&rte_data) == 0)
    {
        Rte_Write_S_ZcRR_SeatCmd_SeatCommand_t(&rte_data);
    }
}

// Data transmission runnable (DataReceivedEvent trigger condition)
// Pattern: MAG generates one runnable per DDS topic the participant publishes
FUNC(void, DdsCdd_CODE) DdsCddWrite_<TopicName>(void)
{
    <TopicType>_t rte_data;
    
    // Read data from RTE port (written by application)
    if (Rte_Read_R_<TopicName>_<TopicType>_t(&rte_data) == E_OK)
    {
        // Forward to adapter for conversion and DDS publishing
        DdsCdd_Adapter_Write_<TopicName>(&rte_data);
    }
}

// Example from ECU_SEAT_ZoneRR: publishing EcuSeat_Status
FUNC(void, DdsCdd_CODE) DdsCddWrite_EcuSeat_Status(void)
{
    SeatStatus_t rte_data;
    if (Rte_Read_R_EcuSeat_Status_SeatStatus_t(&rte_data) == E_OK)
    {
        DdsCdd_Adapter_Write_EcuSeat_Status(&rte_data);
    }
}
```

**Design Pattern**: Delegation pattern — MAG generates runnables that forward calls to the adapter layer functions. Each topic gets its own read or write runnable.

### Layer 2: Adapter Layer

**Files**: `<participant>/adaptation/dds_cdd_adapter.c`, `dds_cdd_adapter.h` (MAG-generated)

**Purpose**: Bridge between AUTOSAR-specific concerns (RTE types, TcpIp, resources) and DDS implementation.

**Responsibilities**:
1. **Type Conversion**: Map between RTE types (received via parameters) and DDS types
2. **TcpIp Integration**: Handle socket owner initialization and IP address management
3. **State Machine**: Manage initialization sequence
4. **System Properties**: Configure AUTOSAR-specific DDS system properties
5. **Resource Management**: Handle AUTOSAR resource allocation
6. **Data Flow Coordination**: Bridge between Layer 1 (RTE interaction) and Layer 3 (DDS operations)

**Initialization State Machine**:

```
TcpIpNotReady
    │
    │ IP address assigned
    ▼
TcpIpReady
    │
    │ Set AUTOSAR system properties
    ▼
SystemPropertiesSet
    │
    │ Create DDS entities (disabled)
    ▼
EntitiesCreated
    │
    │ Enable entities
    ▼
EntitiesEnabled
    │
    │ Normal operation
    ▼
(Running State)
```

**State Machine Implementation**:

```c
typedef enum {
    DDSCDD_STATE_TCPIP_NOT_READY,
    DDSCDD_STATE_TCPIP_READY,
    DDSCDD_STATE_SYSTEM_PROPERTIES_SET,
    DDSCDD_STATE_ENTITIES_CREATED,
    DDSCDD_STATE_ENTITIES_ENABLED
} DdsCdd_StateType;

static DdsCdd_StateType DdsCdd_State = DDSCDD_STATE_TCPIP_NOT_READY;
```

**TcpIp Configuration Note**:

This architecture expects a **static TcpIp configuration** where the local IP address is assigned as soon as TcpIp starts. This design allows the DDS CDD initialization to be triggered before the RTE starts.

- **Static IP systems** (majority of integrations): IP address is immediately assigned when TcpIp initializes, allowing seamless DDS CDD initialization in the expected sequence.
- **Dynamic IP systems** (DHCP): If IP address assignment occurs later in the sequence (after RTE start), the DDS CDD implementation may need adjustment to handle delayed IP assignment. Connext Micro requires the local IP to be assigned prior to fully initializing.

**Key Functions** (generated per participant — topic-specific functions vary):

- `DdsCdd_Adapter_Init()`: Initialize adapter and start state machine
- `DdsCdd_Adapter_Run()`: Advance state machine and maintain DDS QoS protocols
- `DdsCdd_Adapter_Poll_<TopicName>(<Type>_t* rte_data)`: Poll for incoming DDS data and return converted RTE type via parameter
- `DdsCdd_Adapter_Write_<TopicName>(const <Type>_t* rte_data)`: Convert RTE type to DDS and publish
- `DdsCdd_LocalIpAddrAssignmentChg()`: TcpIp callback for IP address changes
- `DdsCdd_RxIndication()`: TcpIp callback for received data

> **Note:** MAG generates one `Poll_` and one `Write_` function per subscribed/published topic. The adapter also contains `TODO` markers where application-specific logic (e.g., custom type field mapping, error handling) may be needed.

### Layer 3: DDS Implementation Layer

**Files**: `<participant>/dds_impl/dds_impl.c`, `dds_impl.h` (MAG-generated)

**Purpose**: Pure DDS logic isolated from AUTOSAR concerns.

**Responsibilities**:
1. **Entity Creation**: Create DomainParticipant, Topics, Publishers, Subscribers, DataWriters, DataReaders
2. **Data Operations**: Write and read DDS samples
3. **QoS Configuration**: Apply QoS policies from XML configuration
4. **DDS Support Code**: Use generated DDS type and application support code from `dds_gen/`

**Key Functions** (generated per participant):

```c
// Create DDS entities (disabled)
int DdsImpl_CreateEntities(void);

// Enable DDS entities for communication
int DdsImpl_EnableEntities(void);

// Take next sample from a DataReader (one sample per call)
// MAG generates one function per subscribed topic
int DdsImpl_<TopicName>_TakeNextSample(<TopicType>* dds_sample, int* is_valid);

// Write sample via DataWriter
// MAG generates one function per published topic
int DdsImpl_<TopicName>_WriteSample(const <TopicType>* dds_sample);
```

**Implementation Details**:

- **Lazy Initialization**: DataReader and DataWriter handles are obtained on first use via function-local static variables
- **Simplified API**: No global state accessors — functions handle their own resource lookup
- **Entity Lookup**: Uses `DDS_DomainParticipant_lookup_datawriter_by_name()` and `DDS_DomainParticipant_lookup_datareader_by_name()`

**Entity Hierarchy** (example for ECU_SEAT_ZoneRR with one published and one subscribed topic):

```
DomainParticipant (ECU_SEAT_ZoneRR)
├── Publisher
│   └── DataWriter (EcuSeat_Status topic)
└── Subscriber
    └── DataReader (ZcRR_SeatCmd topic)
```

MAG generates additional DataWriters/DataReaders for each endpoint defined in the DDS-XML for that participant.

## Communication Flows

### Data Flow: Application → Network (Publishing)

Example using `EcuSeat_Status` topic from the ECU_SEAT_ZoneRR participant:

```
1. Application SW-C
   └─> Rte_Write_S_EcuSeat_Status_SeatStatus_t(&data)
        │
2. RTE Layer
   └─> Triggers DdsCddWrite_EcuSeat_Status runnable via DataReceivedEvent
        │
3. DDS CDD Layer 1 (DdsCdd.c)
   └─> DdsCddWrite_EcuSeat_Status()
   └─> Rte_Read_R_EcuSeat_Status_SeatStatus_t(&rteData)
   └─> Call DdsCdd_Adapter_Write_EcuSeat_Status(&rteData)
        │
4. DDS CDD Layer 2 (Adapter)
   └─> Convert RTE type (SeatStatus_t) to DDS type (SeatStatus)
   └─> Call DdsImpl_EcuSeat_Status_WriteSample(&ddsData)
        │
5. DDS CDD Layer 3 (Implementation)
   └─> Lazy-initialize DataWriter handle (first call)
   └─> SeatStatusDataWriter_write(writer, &sample, ...)
        │
6. DDS Micro
   └─> Serialize and transmit over network
        │
7. TcpIp/Eth Stack
   └─> Physical transmission
```

### Data Flow: Network → Application (Subscribing)

Example using `ZcRR_SeatCmd` topic from the ECU_SEAT_ZoneRR participant:

```
1. TcpIp/Eth Stack
   └─> Receives UDP packet
   └─> Calls DdsCdd_RxIndication()
        │
2. DDS Micro
   └─> Processes received sample
   └─> Stores in DataReader queue
        │
3. DDS CDD Layer 1 (DdsCdd.c)
   └─> DdsCddRead_ZcRR_SeatCmd() periodic runnable executes
   └─> Call DdsCdd_Adapter_Poll_ZcRR_SeatCmd(&rteData)
        │
4. DDS CDD Layer 2 (Adapter)
   └─> Call DdsImpl_ZcRR_SeatCmd_TakeNextSample(&ddsData, &is_valid)
   └─> If valid, convert DDS type to RTE type
   └─> Return converted data via output parameter
        │
5. DDS CDD Layer 1 (DdsCdd.c)
   └─> If DdsCdd_Adapter_Poll_ZcRR_SeatCmd() returns 0:
   └─> Rte_Write_S_ZcRR_SeatCmd_SeatCommand_t(&rteData)
        │
6. RTE Layer
   └─> Stores data in port buffer
        │
7. Application SW-C
   └─> Rte_Read_R_ZcRR_SeatCmd_SeatCommand_t(&data)
   └─> Process received data
```

**Note**: Layer 3 (Implementation) lazily initializes the DataReader handle on first call using a static variable.

## Initialization Sequence

### Detailed Initialization Flow

```
1. TcpIp Stack Initialization
   └─> IP address assigned (static configuration)

2. DdsCdd_Init() [Called by BswM after TcpIp_Init, before Rte_Start]
   ├─> Initialize adapter state machine
   ├─> Set state to TCPIP_NOT_READY or TCPIP_READY (if IP already assigned)
   └─> Register TcpIp callbacks

3. Rte_Start()
   ├─> Initialize all SW-Cs
   └─> Trigger InitEvent condition → DdsCddStart()
        └─> Call DdsCdd_Adapter_Init()

4. DdsCdd_LocalIpAddrAssignmentChg() callback
   └─> State → TCPIP_READY (if not already set)

5. First DdsCddRun() Execution (State: TCPIP_READY)
   ├─> Set AUTOSAR system properties:
   │   ├─> Memory heap allocation
   │   ├─> Resource management hooks
   │   └─> Timer hooks
   └─> State → SYSTEM_PROPERTIES_SET

6. Second DdsCddRun() Execution (State: SYSTEM_PROPERTIES_SET)
   ├─> Call DdsImpl_CreateEntities()
   │   ├─> Register Application Generation plugin (load XML config)
   │   └─> Create DomainParticipant from XML (disabled, with all child entities)
   └─> State → ENTITIES_CREATED

7. Third DdsCddRun() Execution (State: ENTITIES_CREATED)
   ├─> Call DdsImpl_EnableEntities()
   │   └─> Enable DomainParticipant (transitively enables all children)
   └─> State → ENTITIES_ENABLED

8. Normal Operation (State: ENTITIES_ENABLED)
   ├─> DdsCddRun() maintains DDS system (10ms)
   ├─> DdsCddRead_<TopicName>() polls for data per topic (100ms)
   └─> DdsCddWrite_<TopicName>() publishes on trigger per topic
```

### Ordering Constraint

**IMPORTANT REQUIREMENT**: The BswM must initialize modules in this exact sequence:
1. **TcpIp_Init()** - Network stack must be initialized first
2. **DdsCdd_Init()** - DDS CDD must be initialized after TcpIp and before RTE
3. **Rte_Start()** - RTE starts last, after all required BSW modules

**Rationale**: 
- DDS requires IP address to be available before full initialization
- DDS startup time can be significant; initializing before RTE reduces scheduling complexity
- Starting DDS before RTE prevents race conditions during entity creation

**Implementation**: Use BswM to ensure proper ordering in ECU initialization sequence.

**Note**: This ordering assumes static IP configuration. For systems using DHCP (dynamic IP), the `DdsCdd_LocalIpAddrAssignmentChg()` callback handles the state transition when an address is acquired.

## Resource Management

### Memory Architecture

**Static Memory Allocation**:

```c
#define DDSCDD_HEAP_AREA_1_SIZE (240 * 1024)  // 240KB default

static RTI_UINT8 DdsCdd_HeapArea1[DDSCDD_HEAP_AREA_1_SIZE];
```

**Memory Usage**:
- DDS entities (DomainParticipant, Topics, etc.)
- Send/receive buffers
- Discovery protocol data
- QoS policy storage
- Type support metadata

**Sizing**: Memory requirements depend on number of topics, sample sizes, history depth, discovery requirements, and resource limits. Adjust `DDSCDD_HEAP_AREA_1_SIZE` based on your participant's endpoint count and data sizes.

### AUTOSAR Resource Synchronization

**Resource Usage**:

```c
// Resource ID configured in the adapter — must match OS configuration
#define DDS_RESOURCE_START_ID    DDS_Resource001
#define DDS_RESOURCE_COUNT       <N>  // MAG determines count from endpoint configuration

// Resources used for:
// - DDS system operations (mutexes for thread safety)
// - Memory allocation
// - Timer operations
// - Network I/O
```

**Requirements**: `DDS_RESOURCE_COUNT` consecutive STANDARD Resources must be configured in the OS. The exact count depends on the number of endpoints and DDS entities in your participant. MAG generates the required resource ID macro and count; configure your OS (e.g., `OsResource` entries) to match.

### TcpIp Socket Management

**Socket Owner Configuration**:

```c
#define DDSCDD_SOCKET_OWNER_NAME "DdsSocketOwner"
```

**Socket Requirements**:
- 4 UDP sockets (unicast only mode)
- 5 UDP sockets (multicast mode - includes discovery multicast and user data multicast)
- Dynamic port allocation
- Rx indication callback registration

## Timing Architecture

### Runnable Timing Configuration

```
DdsCddStart
├─> Trigger Condition: InitEvent
└─> Execution: Once at startup

DdsCddRun
├─> Trigger Condition: TimingEvent (10ms periodic)
├─> Purpose: DDS QoS maintenance
└─> Tasks: Discovery, liveliness, reliability protocol

DdsCddRead_<TopicName> (one per subscribed topic)
├─> Trigger Condition: TimingEvent (100ms periodic)
├─> Purpose: Poll for incoming data
└─> Tasks: Check DataReader, write to RTE

DdsCddWrite_<TopicName> (one per published topic)
├─> Trigger Condition: DataReceivedEvent on input port
├─> Purpose: Publish data to network
└─> Tasks: Read from RTE, publish via DataWriter
```

**Note:** These trigger conditions are configured in the generated DdsCdd ARXML model. The RTE generator automatically creates the corresponding OS alarms and events from these trigger condition specifications.

**Timing Considerations**:

1. **10ms DdsCddRun Period**:
   - Must be fast enough for DDS protocol maintenance
   - Affects discovery time and reliability protocol
   - Too slow: Increased latency, potential data loss
   - Too fast: Unnecessary CPU overhead

2. **100ms DdsCddRead Period**:
   - Determines maximum data reception rate
   - Should match application requirements
   - Consider jitter and worst-case execution time

3. **DataReceivedEvent Trigger Condition**:
   - Runnable triggered immediately when app writes data to RTE port
   - Minimizes end-to-end latency
   - No polling overhead

### Task Priority Guidelines

DDS CDD runnables should have **higher priority than application SW-Cs** but **lower priority than critical BSW tasks** (Ethernet driver, TcpIp stack). This ensures timely network communication without blocking critical system functions.

## Error Handling Strategy

### Initialization Errors

```c
if (DdsImpl_CreateEntities() != 0) {
    // Log error
    // Remain in current state
    // Retry on next DdsCddRun() cycle
}

if (DdsImpl_EnableEntities() != 0) {
    // Log error
    // Remain in current state  
    // Retry on next DdsCddRun() cycle
}
```

**Strategy**: Retry on next cycle, log errors, graceful degradation

### Runtime Errors

**Write Errors**:
```c
int result = DdsImpl_<TopicName>_WriteSample(&dds_data);
if (result != 0) {
    // Data lost, application should implement retry logic
    // Log error for diagnostics
}
```

**Read Errors**:
```c
int result = DdsImpl_<TopicName>_TakeNextSample(&dds_data, &is_valid);
if (result != 0) {
    // Error reading data, log for diagnostics
} else if (!is_valid) {
    // No new data available (normal condition)
}
```

**Error Propagation**: Errors propagate through return codes, application decides retry strategy

## Scalability Considerations

### Adding Topics

With MAG, adding topics is straightforward:

1. Update `golden_dds_system.xml` and/or `golden_deployment.xml` with new topic/endpoint definitions
2. Re-run MAG (`rtiddsmag -applicationType AUTOSAR_CDD ...`) — this regenerates all three layers
3. Re-run `rtiarcgen` to regenerate ARXML and type support code
4. Reconfigure the RTE generator with updated ARXML
5. Increase memory allocation if needed (more endpoints require more heap)

### Multi-Topic Architecture

```c
// Layer 3: Support multiple topics (lazy initialization per topic)
int DdsImpl_Topic1_TakeNextSample(Type1* dds_sample, int* is_valid);
int DdsImpl_Topic2_TakeNextSample(Type2* dds_sample, int* is_valid);
int DdsImpl_Topic1_WriteSample(const Type1* dds_sample);
int DdsImpl_Topic2_WriteSample(const Type2* dds_sample);

// Layer 2: Multiple adapter functions with parameter passing
int DdsCdd_Adapter_Poll_Topic1(Type1_t* rte_data);
int DdsCdd_Adapter_Poll_Topic2(Type2_t* rte_data);
int DdsCdd_Adapter_Write_Topic1(const Type1_t* rte_data);
int DdsCdd_Adapter_Write_Topic2(const Type2_t* rte_data);

// Layer 1: Multiple runnables with RTE interaction
FUNC(void, DdsCdd_CODE) DdsCddRead_Topic1(void)
{
    Type1_t rte_data;
    if (DdsCdd_Adapter_Poll_Topic1(&rte_data) == 0) {
        Rte_Write_S_Topic1_Type1(&rte_data);
    }
}

FUNC(void, DdsCdd_CODE) DdsCddRead_Topic2(void)
{
    Type2_t rte_data;
    if (DdsCdd_Adapter_Poll_Topic2(&rte_data) == 0) {
        Rte_Write_S_Topic2_Type2(&rte_data);
    }
}

FUNC(void, DdsCdd_CODE) DdsCddWrite_Topic1(void)
{
    Type1_t rte_data;
    if (Rte_Read_R_Topic1_Type1(&rte_data) == E_OK) {
        DdsCdd_Adapter_Write_Topic1(&rte_data);
    }
}

FUNC(void, DdsCdd_CODE) DdsCddWrite_Topic2(void)
{
    Type2_t rte_data;
    if (Rte_Read_R_Topic2_Type2(&rte_data) == E_OK) {
        DdsCdd_Adapter_Write_Topic2(&rte_data);
    }
}
```

## Design Patterns

### 1. Layered Architecture Pattern

**Benefits**:
- Clear separation of concerns
- Testability (each layer can be tested independently)
- Maintainability (changes localized to specific layers)
- Reusability (DDS implementation layer is AUTOSAR-independent)

### 2. State Machine Pattern

**Benefits**:
- Predictable initialization sequence
- Easy to debug and visualize
- Handles asynchronous events (IP address assignment)
- Graceful error recovery

### 3. Adapter Pattern

**Benefits**:
- Decouples RTE types from DDS types
- Isolates AUTOSAR-specific code
- Facilitates porting to different platforms
- Simplifies testing with mock implementations

### 4. Delegation Pattern

**Benefits**:
- RTE template remains simple and stable
- Business logic in easily modifiable adapter layer
- Reduces regeneration impact when ARXML changes