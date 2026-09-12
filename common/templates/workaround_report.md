**Report Version: 1.0.0**
- Generated date: 2026-09-11

**Workaround Report -- snippets with context and line numbers**

- Scope: collected `workaround#` occurrences from all `.vm` files under `templates`.
- Total items found: 38
- Categories: COMMON (23), HAE (13), VTT (2)

Category definitions:
- **COMMON**: Mandatory patch.
- **HAE**: For Autoever only; not a mandatory patch.
- **VTT**: For virtual target (internal only); not a mandatory patch.

Below are code snippets (about +/-5 lines) around each `workaround#` occurrence. Items are grouped by category in this order: COMMON, HAE, VTT.

### COMMON (23)

1) File: templates/autosar/application/autosar_model/application.arxml.vm (L196)
```text
L191:           </CODE-DESCRIPTORS>
L192:           <BEHAVIOR-REF DEST="SWC-INTERNAL-BEHAVIOR">/ComponentTypes/${systemModel.appName}Type/${systemModel.appName}Type_InternalBehavior</BEHAVIOR-REF>
L193:         </SWC-IMPLEMENTATION>
L194:       </ELEMENTS>
L195:     </AR-PACKAGE> ## End of ComponentTypes
L196:     <!-- Workaround#COMMON - delete duplated port inteface definition -->
L197:     <!--
L198:     ## - - - - - - - - - - - - - - - - -
L199:     ## Port Interfaces                 |
L200:     ## - - - - - - - - - - - - - - - - -
L201:     <AR-PACKAGE>
```

2) File: templates/autosar/arxml.xml.vm (L193)
```text
L188:                   #end
L189:                 #end
L190:               #end
L191:                 <TIMING-EVENT>
L192:                   <SHORT-NAME>TMT_DdsCdd_Run</SHORT-NAME>
L193:                   <!-- Workaround#Common - overrun issue -->
L194:                   <START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/TimerTick</START-ON-EVENT-REF>
L195:                   <OFFSET>0.002</OFFSET>
L196:                   <PERIOD>0.01</PERIOD>
L197:                 </TIMING-EVENT>
L198:                 <INIT-EVENT>
```

3) File: templates/autosar/arxml.xml.vm (L224)
```text
L219:                 <INTERNAL-TRIGGER-OCCURRED-EVENT>
L220:                   <SHORT-NAME>ITOE_DdsRxIndication_DataReception_ITP_DummyCallout</SHORT-NAME>
L221:                   <START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/ProcessData</START-ON-EVENT-REF>
L222:                   <EVENT-SOURCE-REF DEST="INTERNAL-TRIGGERING-POINT">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/RxIndication/ITP_DdsCdd_RxIndication</EVENT-SOURCE-REF>
L223:                 </INTERNAL-TRIGGER-OCCURRED-EVENT>
L224:                 <!-- Workaround#Common - overrun issue -->
L225:                 <INTERNAL-TRIGGER-OCCURRED-EVENT>
L226:                   <SHORT-NAME>ITOE_TimerUpdate_ITP_TimerUpdate</SHORT-NAME>
L227:                   <START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/TimerUpdate</START-ON-EVENT-REF>
L228:                   <EVENT-SOURCE-REF DEST="INTERNAL-TRIGGERING-POINT">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/TimerTick/ITP_TimerUpdate</EVENT-SOURCE-REF>
L229:                 </INTERNAL-TRIGGER-OCCURRED-EVENT>
```

4) File: templates/autosar/arxml.xml.vm (L259)
```text
L254:                     </RUNNABLE-ENTITY>
L255:                     #end
L256:                    #end
L257:                   #end
L258:                 #end
L259:                 <!-- Workaround#Common - overrun issue
L260:                 <RUNNABLE-ENTITY>
L261:                   <SHORT-NAME>Run</SHORT-NAME>
L262:                   <CAN-ENTERS>
L263:                     <EXCLUSIVE-AREA-REF-CONDITIONAL>
L264:                       <EXCLUSIVE-AREA-REF DEST="EXCLUSIVE-AREA">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/ExclusiveArea_tick</EXCLUSIVE-AREA-REF>
L265:                     </EXCLUSIVE-AREA-REF-CONDITIONAL>
L266:                     <EXCLUSIVE-AREA-REF-CONDITIONAL>
L267:                       <EXCLUSIVE-AREA-REF DEST="EXCLUSIVE-AREA">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/ExclusiveArea_system</EXCLUSIVE-AREA-REF>
L268:                     </EXCLUSIVE-AREA-REF-CONDITIONAL>
L269:                   </CAN-ENTERS>
L270:                   <MINIMUM-START-INTERVAL>0</MINIMUM-START-INTERVAL>
L271:                   <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
L272:                   <SYMBOL>Run</SYMBOL>
L273:                 </RUNNABLE-ENTITY>
L274:                 -->
L275:                 <!-- Workaround#Common - overrun issue -->
L276:                 <RUNNABLE-ENTITY>
L277:                   <SHORT-NAME>TimerTick</SHORT-NAME>
L278:                   <CAN-ENTERS>
L279:                     <EXCLUSIVE-AREA-REF-CONDITIONAL>
```

5) File: templates/autosar/arxml.xml.vm (L275)
```text
L270:                   <MINIMUM-START-INTERVAL>0</MINIMUM-START-INTERVAL>
L271:                   <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
L272:                   <SYMBOL>Run</SYMBOL>
L273:                 </RUNNABLE-ENTITY>
L274:                 -->
L275:                 <!-- Workaround#Common - overrun issue -->
L276:                 <RUNNABLE-ENTITY>
L277:                   <SHORT-NAME>TimerTick</SHORT-NAME>
L278:                   <CAN-ENTERS>
L279:                     <EXCLUSIVE-AREA-REF-CONDITIONAL>
L280:                       <EXCLUSIVE-AREA-REF DEST="EXCLUSIVE-AREA">/ComponentTypes/DdsCddType/DdsCddType_InternalBehavior/ExclusiveArea_tick</EXCLUSIVE-AREA-REF>
```

6) File: templates/autosar/arxml.xml.vm (L359)
```text
L354:                       <SHORT-NAME>ITP_DdsCdd_RxIndication</SHORT-NAME>
L355:                       <SW-IMPL-POLICY>STANDARD</SW-IMPL-POLICY>
L356:                     </INTERNAL-TRIGGERING-POINT>
L357:                   </INTERNAL-TRIGGERING-POINTS>
L358:                 </RUNNABLE-ENTITY>
L359:                 <!-- Workaround#Common - overrun issue -->
L360:                 <RUNNABLE-ENTITY>
L361:                   <SHORT-NAME>TimerUpdate</SHORT-NAME>
L362:                 </RUNNABLE-ENTITY>
L363:               </RUNNABLES>
L364:               <SUPPORTS-MULTIPLE-INSTANTIATION>false</SUPPORTS-MULTIPLE-INSTANTIATION>
```

7) File: templates/autosar/CDD/adaptation/dds_cdd_adapter.c.vm (L44)
```text
L39:  *============================================================================*/
L40: 
L41: /**
L42:  * @brief Current DDS initialization state (NOT configurable)
L43:  */
L44:  /* workaround#COMMON - task overrun issue */
L45: DdsCdd_InitState_t dds_cdd_init_state = DdsCdd_InitState_Uninitialized;
L46: 
L47: /*==============================================================================
L48:  *                     SW-C RUNNABLE IMPLEMENTATIONS
L49:  *============================================================================*/
```

8) File: templates/autosar/CDD/adaptation/dds_cdd_adapter.h.vm (L36)
```text
L31: /**
L32:  * @brief DDS initialization state tracking
L33:  */
L34: typedef enum
L35: {
L36:     /* workaround#COMMON - task overrun issue */
L37:     //DdsCdd_InitState_TcpIpNotReady = 0,
L38:     //DdsCdd_InitState_TcpIpReady,
L39:     DdsCdd_InitState_Uninitialized = 0,
L40: 
L41:     DdsCdd_InitState_SystemPropertiesSet,
```

9) File: templates/autosar/CDD/adaptation/dds_cdd_adapter.h.vm (L129)
```text
L124:  * 
L125:  * Sets system properties and creates DDS entities.
L126:  */
L127: void DdsCdd_Adapter_Init(void);
L128: 
L129: /* workaround#COMMON - task overrun issue */
L130: /**
L131:  * @brief Enable DDS entities
L132:  * 
L133:  * Enables DDS entities after creation.
L134:  */
```

10) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L80)
```text
L75: ${hashtag}if defined(_MSC_VER) && !defined(__at)
L76: ${hashtag}define __at(address)
L77: ${hashtag}endif
L78: ${hashtag}endif
L79: 
L80: /* workaround#COMMON - Some RTI Micro 4.3.0 header sets do not expose these prototypes publicly. */
L81: RTI_BOOL OSPSL_AutosarSystem_get_property(struct OSAPI_SystemAutosar *property);
L82: RTI_BOOL OSPSL_AutosarSystem_set_property(struct OSAPI_SystemAutosar *property);
L83: 
L84: #end
L85: 
```

11) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L192)
```text
L187:             RTI_TRUE; /* TODO: Default is not thread safe, change to true if using multithread */
L188:     
L189:     /* Connext DDS Micro will use Resources as synchronization method */
L190:     system_property.psl_property.sync_type = OSAPI_AUTOSAR_SYNCKIND_RESOURCES;
L191:     system_property.psl_property.mutex_resource_id = ${autosarConfig.getMutexResourceId()};
L192:     /* workaround#COMMON - task overrun issue */
L193:     system_property.psl_property.timer_resource_id = OsResource_DdsTimer;
L194:     system_property.psl_property.netio_resource_id = OsResource_DdsNetio;
L195:     
L196:     /* AUTOSAR synchronization configuration - Resources only */
L197:     system_property.psl_property.semaphore_max_count = 0;
```

12) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L260)
```text
L255:  * @post DDS entities created but disabled if successful
L256:  */
L257: void DdsCdd_Adapter_Init(void)
L258: {
L259:     sint8 retval;
L260:     /* workaround#COMMON - task overrun issue */
L261:     //printf("DDS_Init: Start Init DDS \n");
L262: 
L263:     /* Check if TcpIp is ready */
L264:     //if (dds_cdd_init_state == DdsCdd_InitState_TcpIpNotReady || 
L265:     //    dds_cdd_init_state == DdsCdd_InitState_Error)
```

13) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L272)
```text
L267:     //    printf("DDS_Init: TcpIp not ready or error state\n");
L268:     //    return;
L269:     //}
L270: 
L271:     /* Set system properties */
L272:     /* workaround#COMMON - task overrun issue */
L273:     //if (dds_cdd_init_state == DdsCdd_InitState_TcpIpReady)
L274:     //{
L275:         printf("DDS_Init: Setting system properties\n");
L276:         if (0 != SetSystemProperties())
L277:         {
```

14) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L282)
```text
L277:         {
L278:             printf("DDS_Init: Failed to set system properties\n");
L279:             dds_cdd_init_state = DdsCdd_InitState_Error;
L280:             return;
L281:         }
L282:         /* Workaround#COMMON - PIL option error */
L283: ${hashtag}if 0
L284:         //original implementation
L285:         else if(RTI_TRUE != OSAPI_System_initialize())
L286:         {
L287:             printf("DDS_Init: OSAPI_System initialization failed\n");
```

15) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L339)
```text
L334: 
L335: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L336: ## macro to define the DdsCdd_Adapter_Enable_DDSEntities function
L337: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L338: #macro( ddsCddAdapterC_DdsCdd_Adapter_Enable_DDSEntities  )
L339: /* workaround#COMMON - task overrun issue */
L340: /**********************************************************************************************************************
L341:  * DdsCdd_Adapter_Enable_DDSEntities()
L342:  *********************************************************************************************************************/
L343: /**
L344:  * @brief Enable DDS entities
```

16) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L382)
```text
L377: 
L378: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L379: ## macro to define the DdsCdd_Adapter_Run function
L380: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L381: #macro( ddsCddAdapterC_DdsCdd_Adapter_Run )
L382: /* workaround#COMMON - task overrun issue */
L383: /**********************************************************************************************************************
L384:  * DdsCdd_Adapter_Run()
L385:  *********************************************************************************************************************/
L386: /**
L387:  * @brief Maintain DDS timer
```

17) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L457)
```text
L452:     if (is_valid)
L453:     {
L454:         /* Valid sample received */
L455:         printf("DdsCdd_Adapter_Read_${topic}: Valid sample received\n");
L456: 
L457:         /* Convert DDS type (dds_${type}) to AUTOSAR type (${type}) */ /* workaround#COMMON - delete & of rte_data */
L458:         ${type}_dds_to_rte(&dds_sample, rte_data);
L459:         return 0;
L460:     }
L461:     else
L462:     {
```

18) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L577)
```text
L572: {
L573:     printf("[RTI] DDS_LocalIpAddrAssignmentChg %u:%u!\n", LocalAddrId, State);
L574:     NETIO_Autosar_update_ip_assignment_state(LocalAddrId, State);
L575:     if((State == TCPIP_IPADDR_STATE_ASSIGNED))
L576:     {
L577:         /* workaround#COMMON - task overrun issue */
L578:         //if ((dds_cdd_init_state == DdsCdd_InitState_TcpIpNotReady) && (LocalAddrId == 0))
L579:         //{
L580:         //    printf("TCP/IP is ready - allow DDS initialization\n");
L581:         //    dds_cdd_init_state = DdsCdd_InitState_TcpIpReady;
L582:         //}
```

19) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L119)
```text
L114:             #end
L115:         #end
L116:     #end
L117: #end
L118: 
L119: /* workaround#COMMON - task overrun issue */
L120: /**********************************************************************************************************************
L121:  *
L122:  * Runnable Entity Name: TimerTick
L123:  *
L124:  *---------------------------------------------------------------------------------------------------------------------
```

20) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L164)
```text
L159: /**********************************************************************************************************************
L160:  * DO NOT CHANGE THIS COMMENT!           << End of runnable implementation >>               DO NOT CHANGE THIS COMMENT!
L161:  *********************************************************************************************************************/
L162: }
L163: 
L164: /* workaround#COMMON - task overrun issue */
L165: /**********************************************************************************************************************
L166:  *
L167:  * Runnable Entity Name: TimerUpdate
L168:  *
L169:  *---------------------------------------------------------------------------------------------------------------------
```

21) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L270)
```text
L265: {
L266: /**********************************************************************************************************************
L267:  * DO NOT CHANGE THIS COMMENT!           << Start of runnable implementation >>             DO NOT CHANGE THIS COMMENT!
L268:  * Symbol: DdsCddStart
L269:  *********************************************************************************************************************/
L270:     /* workaround#COMMON - task overrun issue */
L271:     /* Enable DDS Entities */
L272:     DdsCdd_Adapter_Enable_DDSEntities();
L273: 
L274: /**********************************************************************************************************************
L275:  * DO NOT CHANGE THIS COMMENT!           << End of runnable implementation >>               DO NOT CHANGE THIS COMMENT!
```

22) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L289)
```text
L284:             #end
L285:         #end
L286:     #end
L287: #end
L288: 
L289: /* workaround#COMMON - wrong position, DdsCdd_Init placed outside. */
L290: ${hashtag}if 0
L291: ${hashtag}define DdsCdd_STOP_SEC_CODE
L292: ${hashtag}include "DdsCddType_MemMap.h" /* PRQA S 5087 */ /* MD_MSR_MemMap */
L293: ${hashtag}endif
L294: 
```

23) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L302)
```text
L297:  *********************************************************************************************************************/
L298: 
L299:   FUNC(void, DdsCdd_CODE) DdsCdd_Init(void) 
L300: {
L301:   /* TODO: Create entities once micro allows doing so before rte*/
L302:   /* workaround#COMMON - task overrun issue */
L303:   /* Initialize DDS adapter layer */
L304:   DdsCdd_Adapter_Init();    //This function will be called by EcuM directly before StartOs.
L305: }
L306: 
L307: /* workaround#HAE - right position and senction name */
```

### HAE (13)

24) File: templates/autosar/application/autosar_model/application.arxml.vm (L65)
```text
L60:                   <DATA-ELEMENT-REF DEST="VARIABLE-DATA-PROTOTYPE">/PortInterfaces/${topic}/${type}</DATA-ELEMENT-REF>
L61:                   <HANDLE-OUT-OF-RANGE>NONE</HANDLE-OUT-OF-RANGE>
L62:                   <USES-END-TO-END-PROTECTION>false</USES-END-TO-END-PROTECTION>
L63:                   <ALIVE-TIMEOUT>0</ALIVE-TIMEOUT>
L64:                   <ENABLE-UPDATE>false</ENABLE-UPDATE>
L65:                   <!-- Workaround#HAE - delete unnecessary elements
L66:                   <FILTER>
L67:                     <DATA-FILTER-TYPE>ALWAYS</DATA-FILTER-TYPE>
L68:                   </FILTER>
L69:                   -->
L70:                   <HANDLE-NEVER-RECEIVED>false</HANDLE-NEVER-RECEIVED>
L71:                   <INIT-VALUE>
L72:                     <RECORD-VALUE-SPECIFICATION>
L73:                       <FIELDS>
L74:                         <NUMERICAL-VALUE-SPECIFICATION>
```

25) File: templates/autosar/arxml.xml.vm (L88)
```text
L83:                     <NONQUEUED-RECEIVER-COM-SPEC>
L84:                       <DATA-ELEMENT-REF DEST="VARIABLE-DATA-PROTOTYPE">/PortInterfaces/$datawriter.topicName/$datawriter.typeRef</DATA-ELEMENT-REF>
L85:                       <USES-END-TO-END-PROTECTION>false</USES-END-TO-END-PROTECTION>
L86:                       <ALIVE-TIMEOUT>0</ALIVE-TIMEOUT>
L87:                       <ENABLE-UPDATE>false</ENABLE-UPDATE>
L88:                       <!-- Workaround#HAE - delete unnecessary elements
L89:                       <FILTER>
L90:                         <DATA-FILTER-TYPE>ALWAYS</DATA-FILTER-TYPE>
L91:                       </FILTER>
L92:                       -->
L93:                       <HANDLE-NEVER-RECEIVED>false</HANDLE-NEVER-RECEIVED>
L94:                       <INIT-VALUE>
L95:                         <RECORD-VALUE-SPECIFICATION>
L96:                           <FIELDS>
L97:                             <NUMERICAL-VALUE-SPECIFICATION>
```

26) File: templates/autosar/arxml.xml.vm (L411)
```text
L406:                 </SW-DATA-DEF-PROPS-VARIANTS>
L407:               </SW-DATA-DEF-PROPS>
L408:               <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/dds/$topicEntry.get(1)</TYPE-TREF>
L409:               </VARIABLE-DATA-PROTOTYPE>
L410:             </DATA-ELEMENTS>
L411:             <!-- Workaround#HAE - delete unnecessary elements
L412:             <INVALIDATION-POLICYS>
L413:               <INVALIDATION-POLICY>
L414:               <DATA-ELEMENT-REF DEST="VARIABLE-DATA-PROTOTYPE">/PortInterfaces/$topicEntry.get(0)/$topicEntry.get(1)</DATA-ELEMENT-REF>
L415:               <HANDLE-INVALID>DONT-INVALIDATE</HANDLE-INVALID>
L416:               </INVALIDATION-POLICY>
L417:             </INVALIDATION-POLICYS>
L418:             -->
L419:           </SENDER-RECEIVER-INTERFACE>
L420:         #end
L421:       </ELEMENTS>
L422:     </AR-PACKAGE>
L423:   </AR-PACKAGES>
```

27) File: templates/autosar/CDD/adaptation/dds_cdd_adapter.c.vm (L77)
```text
L72: /*==============================================================================
L73:  *                        SOCKET OWNER INTEGRATION
L74:  *============================================================================*/
L75: 
L76: /* TcpIp_[SocketOwnerName]GetSocket - TODO: update if using different SocketOwner name */
L77: /* Workaround#HAE - mobilgene naming rule, prefix TcpIp_ */
L78: ${hashtag}define DDSCDD_SOCKET_OWNER_GET_SOCKET   TcpIp_TcpIp_DdsCddGetSocket   /* TcpIp_socket_name = TcpIp_DdsCdd */
L79: 
L80: #ddsCddAdapterC_DdsCdd_GetSocket()
L81: 
L82: #ddsCddAdapterC_DdsCdd_LocalIpAddrAssignmentChg()
```

28) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L126)
```text
L121: /**
L122:  * @brief Static heap area 1 buffer
L123:  * 
L124:  * Pre-allocated static buffer for DDS memory management.
L125:  */
L126:  /* Workaround#HAE - empty start_address doesn't need at() */
L127:     #foreach( $heap in $heaps )
L128:     #set( $heapStartAddress = "$!heap.getStartAddress()" )
L129:     #if( $heapStartAddress.trim().length() > 0 )
L130: static char heap_area${foreach.count}[DDSCDD_${heap.getName().toUpperCase()}_SIZE] __at(${heap.getStartAddress()});
L131:     #else
```

29) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L185)
```text
L180:     
L181:     /* Configure static memory heap areas */
L182:     system_property.psl_property.number_of_heap_areas = DDSCDD_NUMBER_OF_HEAP_AREAS;
L183:     system_property.psl_property.heap_area_size = heap_area_size;
L184:     system_property.psl_property.heap_area = (const char **)heap_area;
L185:     /* workaround#HAE - enable use_udp_thread */
L186:     system_property.psl_property.enable_thread_safe_heap =
L187:             RTI_TRUE; /* TODO: Default is not thread safe, change to true if using multithread */
L188:     
L189:     /* Connext DDS Micro will use Resources as synchronization method */
L190:     system_property.psl_property.sync_type = OSAPI_AUTOSAR_SYNCKIND_RESOURCES;
```

30) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L213)
```text
L208:     ${hashtag}else
L209:         system_property.psl_property.max_receive_sockets = 2;  /* Unicast only */
L210:     ${hashtag}endif
L211:     
L212:     /* Disable internal UDP buffers - use AUTOSAR TcpIp stack buffers */
L213:     /* workaround#HAE - enable use_udp_thread */
L214:     system_property.psl_property.number_of_rcv_buffers = 8u;
L215:     system_property.psl_property.rcv_buffer_size = 1500u;
L216:     
L217:     /* Set AUTOSAR TcpIp integration callbacks */
L218:     system_property.psl_property.get_socket = DdsCdd_GetSocket;
```

31) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L225)
```text
L220:     system_property.psl_property.max_local_addr_id = ${autosarConfig.getMaxLocalAddrId()};
L221: 
L222:     system_property.psl_property.send_local_addr_id = ${autosarConfig.getSendLocalAddrId()};
L223:     
L224:     /* Configure UDP thread handling - use synchronous mode for AUTOSAR */
L225:     /* workaround#HAE - enable use_udp_thread */
L226:     system_property.psl_property.use_udp_thread = TRUE;
L227:     system_property.psl_property.dds_rxindication =
L228:             DdsCddRxIndication;  /* TODO: Default name for dds rx indication, change if using custom callback */
L229: 
L230:     if (!OSPSL_AutosarSystem_set_property(&system_property))
```

32) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.h.vm (L117)
```text
L112:     ${hashtag}include "Std_Types.h"
L113:     ${hashtag}include "Os_Cfg.h"
L114:     ${hashtag}include "TcpIp.h"
L115:     ${hashtag}include "Rte_DdsCddType.h"  /* Provides ${inputFilePlugin} type definition and RTE function signatures */
L116: 
L117:     /* workaround#HAE */
L118:     /* RTI DDS Micro includes are intentionally kept out of this public header.
L119:     * Include them in implementation files only to avoid macro conflicts with
L120:     * AUTOSAR compiler abstraction (e.g., CONST/VAR macros). */
L121:     ${hashtag}ifndef VVIRTUALTARGET
L122:     ${hashtag}include "dds_impl.h"
```

33) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.h.vm (L125)
```text
L120:     * AUTOSAR compiler abstraction (e.g., CONST/VAR macros). */
L121:     ${hashtag}ifndef VVIRTUALTARGET
L122:     ${hashtag}include "dds_impl.h"
L123:     ${hashtag}endif
L124: 
L125:     /* workaround#HAE - add an user_stub header file */
L126:     ${hashtag}include "dds_cdd_userstub.h" //SHOULD BE CREATED EXTERNALLY
L127: #end
L128: 
L129: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L130: ## macro to declare write functions that RTE will call when application writes to RTE
```

34) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L66)
```text
L61: /**********************************************************************************************************************
L62:  * DO NOT CHANGE THIS COMMENT!           << End of include and declaration area >>          DO NOT CHANGE THIS COMMENT!
L63:  *********************************************************************************************************************/
L64: 
L65: 
L66: /* workaround#HAE - section naming rule */
L67: ${hashtag}ifdef VVIRTUALTARGET
L68: ${hashtag}define DdsCdd_START_SEC_CODE
L69: ${hashtag}else
L70: ${hashtag}define DdsCddType_START_SEC_CODE
L71: ${hashtag}endif
```

35) File: templates/autosar/CDD/autosar_gen/DdsCdd.c.vm (L307)
```text
L302:   /* workaround#COMMON - task overrun issue */
L303:   /* Initialize DDS adapter layer */
L304:   DdsCdd_Adapter_Init();    //This function will be called by EcuM directly before StartOs.
L305: }
L306: 
L307: /* workaround#HAE - right position and senction name */
L308: ${hashtag}ifdef VVIRTUALTARGET
L309: ${hashtag}define DdsCdd_STOP_SEC_CODE
L310: ${hashtag}else
L311: ${hashtag}define DdsCddType_STOP_SEC_CODE
L312: ${hashtag}endif
```

36) File: templates/autosar/CDD/dds_impl/dds_impl_macro.h.vm (L56)
```text
L51:     ${hashtag}include "#headerInclude()${typeFilePrefix}.h"  /* DDS type definition generated from IDL */
L52:              
L53:         ${hashtag}if (OSAPI_ENABLE_LOG == 1 && OSAPI_ENABLE_TRACE == 1)
L54:             /* TODO: Depend on each platform, change to appropriate logging function */
L55:             //${hashtag}define printf serialprintf
L56:             /* workaround#HAE - don't use serialprintf */
L57:             ${hashtag}define printf(...) do {} while(0) 
L58:         /* Woraround#VTT - cprintf */
L59:         ${hashtag}elif VVIRTUALTARGET
L60:             extern void CANoeAPI_Printf(const char*, ...);
L61:             ${hashtag}define cprintf CANoeAPI_Printf
```

### VTT (2)

37) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L48)
```text
L43: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L44: ## macro to include necessary headers for the adapter implementation
L45: ## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
L46: #macro( ddsCddAdapterC_IncludeHeaders $inputFilePlugin)
L47: 
L48: /* Workaround#VTT */
L49: /* Pull RTI/Windows headers first to avoid AUTOSAR macro pollution. */
L50: ${hashtag}if defined(_WIN32) || defined(_WIN64) || defined(RTI_WIN32)
L51: ${hashtag}define SetEvent Win32_SetEvent
L52: ${hashtag}include "../dds_impl/dds_impl.h"
L53: ${hashtag}undef SetEvent
```

38) File: templates/autosar/CDD/adaptation/dds_cdd_adapter_macro.c.vm (L72)
```text
L67: 
L68: ${hashtag}ifndef netio_common_h
L69: ${hashtag}include "netio/netio_common.h"
L70: ${hashtag}endif
L71: 
L72: /* Workaround#VTT */
L73: /* __at(address) is a target-specific placement extension not supported by MSVC. */
L74: ${hashtag}if defined(_WIN32) || defined(_WIN64) || defined(RTI_WIN32)
L75: ${hashtag}if defined(_MSC_VER) && !defined(__at)
L76: ${hashtag}define __at(address)
L77: ${hashtag}endif
```
