/*
 * FILE: autosarSystem.c - AutoSAR system functionality
 *
 * Copyright 2019-2026 Real-Time Innovations, Inc.
 *
 * All rights reserved.
 *
 * No duplications, whole or partial, manual or electronic, may be made
 * without express written permission.  Any such copies, or
 * revisions thereof, must display this notice unaltered.
 * This code contains trade secrets of Real-Time Innovations, Inc.
 *
 * Modification History
 * --------------------
 * 13dec2021,tk MICRO-3226/PR.29479
 * - Made uuid_counter global and renamed to OSAPI_System_fv_UuidCounter
 *   to comply with the coding standards.
 * 03aug2021,tk MICRO-2953/PR.28897
 *  - Added parentheses around bitwise &  in
 *    OSAPI_SystemAutosar_check_semaphore_properties
 * 22jul2021,fmt MICRO-2953/PR.28897
 *  - Corrected test for upper bound for available alarm ids.
 * 13apr2021,tk MICRO-3028/PR.28960
 * - Added robustness check for OSAPI_System_get_native_interface
 * 15mar2021,fmt MICRO-2953/PR#28897
 *    - Add check for correctness of event ids.
 * 21feb2021,tk MICRO-2444/PR#27674
 *   - Added comment to OSAPI_AutosarSystem_generate_uuid() explaining
 *     why an overflow of uuid_counter is not possible for RTI_CERT.
 * 13jan2021,tk MICRO-2807/PR27549 Removed unused functions for CERT.
 * 21dec2020,fmt MICRO-2771/PR.28498
 *    - Fix OSAPI_AutosarSystem_get_ticktime() to return nanoseconds
 *      instead of microseconds.
 * 9dec2020,fmt MICRO-2724/PR.28425
 *     - Check return value of OSAPI_System_lock() in
 *       OSAPI_SystemAutosar_timer_callback()
 * 26nov2020,fmt MICRO-2698/PR.28313
 *    - Fix use of type TcpIp_SockAddrType in
 *      function OSAPI_AutosarSystem_get_ip_address()
 * 16oct2020,tk MICRO-2609/PR.28209
 *    - Renamed field number_of_sockets to max_receive_sockets
 * 6oct2020,fmt MICRO-2585/PR.28155
 *    - Add consistency check of all Autosar port properties in
 *      OSAPI_SystemAutosar_initialize()
 * 1oct2020,fmt MICRO-2588/PR.28170
 *    - Align (OSAPI_SystemAutosar_timer_callback) with Micro for consistency
 * 25aug2020,fmt MICRO-2500/PR.28028
 *    - The AUTOSAR port does not check the return value for AUTOSAR API calls
 * 21may2020,fmt MICRO-2409/PR.27650 Exclude from cert build finalize() functions
 * 07may2020,fmt MICRO-2342/PR.27592 Use IP address to generate UUID
 * 13mar2019,fmt Rewritten
 *
 */
/*ce
 * \file
 * \brief AutoSAR implementation of OSAPI system routines
 */
#include "rti_me_psl.h"

#include "autosarMutex.h"
#include "autosarSemaphore.h"
#include "autosarHeap.h"

/*ci \brief Timer resolution in milliseconds.
 */
#define OSAPISYSTEM_TIMER_RESOLUTION_MS \
    (OSAPI_System_gv_PortProperty->timer_resolution_ms)

/*ci \brief Timer resolution in microseconds.
 */
#define OSAPISYSTEM_TIMER_RESOLUTION_US \
    (OSAPISYSTEM_TIMER_RESOLUTION_MS * OSAPI_TIME_USEC_PER_MSEC)

/*ci \brief Timer resolution in nanoseconds.
 */
#define OSAPISYSTEM_TIMER_RESOLUTION_NS \
    (OSAPISYSTEM_TIMER_RESOLUTION_MS * OSAPI_TIME_NSEC_PER_MSEC)

/*ci \brief Initialize for the OSAPI_SystemTimerHandler
 */
#define OSAPI_SystemTimerHandler_INITIALIZER \
{ \
    NULL,\
    NULL,\
}

/*ci \brief Initialize for the OSAPI_SystemAutosar
 */

#ifndef RTI_CERT
#define OSAPI_SystemAutosar_INITIALIZER \
{ \
    OSAPI_System_INITIALIZER, \
    RTI_FALSE, \
    { OSAPI_SystemTimerHandler_INITIALIZER }, \
    0,\
    NULL,\
    0,\
    0,\
    0,\
    NULL,\
}
#else
#define OSAPI_SystemAutosar_INITIALIZER \
{ \
    OSAPI_System_INITIALIZER, \
    { OSAPI_SystemTimerHandler_INITIALIZER }, \
    0,\
    NULL,\
    0,\
    0,\
    0,\
    NULL,\
}
#endif

/*ci \brief Size of the Autosar system structure.
 */
RTI_UINT32 OSAPI_System_gv_Size = sizeof(struct OSAPI_SystemAutosar);

/*ci \brief Autosar System variable.
 */
RTI_PRIVATE struct OSAPI_SystemAutosar OSAPI_System_g_autosar = OSAPI_SystemAutosar_INITIALIZER;

/*ci \brief Pointer to Autosar System variable.
 */
RTI_PRIVATE struct OSAPI_SystemAutosar *OSAPI_System_fv_SystemAutosar =
    &OSAPI_System_g_autosar;


/*ci \brief Pointer to System.
 */
P2VAR(struct OSAPI_System, AUTOMATIC, SOAD_APPL_DATA)
OSAPI_System_gv_System = &OSAPI_System_g_autosar._parent;

struct OSAPI_LogEntryI *OSAPI_Log_gv_LogIntf = NULL;

/*ci \brief Pointer to Autosar System property.
 */
P2VAR(struct OSAPI_PortProperty, AUTOMATIC, SOAD_APPL_DATA)
OSAPI_System_gv_PortProperty = &OSAPI_System_g_autosar.psl_property;

/*ci \brief Global counter to create UUID, incremented in each call to generate
 *   a UUID.
 */
RTI_PRIVATE RTI_UINT32 OSAPI_System_fv_UuidCounter = 0xdeadc0de;


/*** SOURCE_BEGIN ***/

/*ci
 * \brief Check the consistency of the heap properties.
 *
 * \return TRUE if heap properties are consistent.
 *         FALSE if heap properties are not consistent.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_check_heap_properties(void)
{
    uint32 i;

    if ((OSAPI_System_gv_PortProperty->number_of_heap_areas == 0) ||
        (OSAPI_System_gv_PortProperty->heap_area_size == NULL_PTR) ||
        (OSAPI_System_gv_PortProperty->heap_area == NULL_PTR))
    {
        return FALSE;
    }

    for (i = 0; i < OSAPI_System_gv_PortProperty->number_of_heap_areas; i++)
    {
        if ((OSAPI_System_gv_PortProperty->heap_area_size[i] == 0) ||
            (OSAPI_System_gv_PortProperty->heap_area[i] == NULL_PTR))
        {
            return FALSE;
        }
    }

    /* First area has to be big enough to hold at least offsets for all memory
     * areas. Also it is possible that the first area is not aligned to
     * sizeof(uint32). For simplicity just add 1 to the number of areas to
     * consider alignment.
     */
    if (OSAPI_System_gv_PortProperty->heap_area_size[0] <
        (sizeof(uint32) *
         (OSAPI_System_gv_PortProperty->number_of_heap_areas + 1)))
    {
        return FALSE;
    }

    return TRUE;
}

/*ci
 * \brief Check the consistency of the mutex properties.
 *
 * \return TRUE if mutex properties are consistent.
 *         FALSE if mutex properties are not consistent.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_check_mutex_properties(void)
{
    if (OSAPI_System_gv_PortProperty->sync_type ==
        OSAPI_AUTOSAR_SYNCKIND_RESOURCES)
    {
        /* ResourceId 0 is reserved for EcuM */
        if (OSAPI_System_gv_PortProperty->mutex_resource_id == 0)
        {
            return FALSE;
        }
    }

    return TRUE;
}

/*ci
 * \brief Check the consistency of the semaphore properties.
 *
 * \return TRUE if semaphore properties are consistent.
 *         FALSE if semaphore properties are not consistent.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_check_semaphore_properties(void)
{
    if (OSAPI_System_gv_PortProperty->semaphore_max_count != 0)
    {
        EventMaskType event_id;
        EventMaskType greater_id;
        EventMaskType smaller_id;
        RTI_UINT32 i = 0;
        RTI_UINT32 alarm_max_value;

        if ((OSAPI_System_gv_PortProperty->first_give_event == 0) ||
            (OSAPI_System_gv_PortProperty->first_timeout_event == 0) ||
            (OSAPI_System_gv_PortProperty->first_give_event ==
             OSAPI_System_gv_PortProperty->first_timeout_event) ||
            (OSAPI_System_gv_PortProperty->first_alarm == 0))
        {
            return FALSE;
        }

        /* Event id must be a multiple of 2.
         * According to
         * http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2
         * Note that we already checked that neither of the event ids is 0.
         */
        if ((OSAPI_System_gv_PortProperty->first_give_event &
             (OSAPI_System_gv_PortProperty->first_give_event - 1)) != 0)
        {
            return FALSE;
        }
        if ((OSAPI_System_gv_PortProperty->first_timeout_event &
             (OSAPI_System_gv_PortProperty->first_timeout_event - 1)) != 0)
        {
            return FALSE;
        }

        /* Operation (first event << (semaphore_max_count - 1)) can not overflow
         * the size of EventMaskType. So the configuration is wrong if the
         * number of bits in type of
         * OSAPI_System_gv_PortProperty->first_give_event
         * is smaller than the 0-index of enabled bit in max(first_give_event,
         * first_timeout_event) + semaphore_max_count.
         */
        if (OSAPI_System_gv_PortProperty->first_timeout_event >
            OSAPI_System_gv_PortProperty->first_give_event)
        {
            event_id = OSAPI_System_gv_PortProperty->first_timeout_event;
            greater_id = OSAPI_System_gv_PortProperty->first_timeout_event;
            smaller_id = OSAPI_System_gv_PortProperty->first_give_event;
        }
        else
        {
            event_id = OSAPI_System_gv_PortProperty->first_give_event;
            greater_id = OSAPI_System_gv_PortProperty->first_give_event;
            smaller_id = OSAPI_System_gv_PortProperty->first_timeout_event;
        }
        while ((event_id & 0x1U) == 0)
        {
            event_id = event_id >> 1;
            i++;
        }
        /* 8 bits in a byte */
        if  ((i + OSAPI_System_gv_PortProperty->semaphore_max_count) >
             (sizeof(OSAPI_System_gv_PortProperty->first_give_event) * 8))
        {
            return FALSE;
        }

        /* The number of bits between index of bit set in first_give_event
         * and index of bit set in first_timeout_event can not be smaller
         * than semaphore_max_count
         */
        i = 0;
        while ((smaller_id & greater_id) == 0)
        {
            smaller_id = smaller_id << 1;
            i++;
        }
        if (OSAPI_System_gv_PortProperty->semaphore_max_count > i)
        {
            return FALSE;
        }

        /* Size of type AlarmType might be different on different AUTOSAR
         * implementations. So we need to calculate the maximum value of
         * an alarm ID during runtime, and take care of possible
         * overflows.
         */
        alarm_max_value = (((1U <<
                             (sizeof(OSAPI_System_gv_PortProperty->first_alarm)
                                    * 8 - 1U)) - 1U) << 1U) | 0x1;

        /* We already checked that first_alarm is not 0, so next operation
         * can not overflow
         */
        if ((alarm_max_value - OSAPI_System_gv_PortProperty->first_alarm + 1) <
                        OSAPI_System_gv_PortProperty->semaphore_max_count)
        {
            return FALSE;
        }
    }

    return TRUE;
}

/*ci
 * \brief Check the consistency of the socket properties.
 *
 * \return TRUE if socket properties are consistent.
 *         FALSE if socket properties are not consistent.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_check_socket_properties(void)
{
    if ((OSAPI_System_gv_PortProperty->use_socket_owner == TRUE) &&
        (OSAPI_System_gv_PortProperty->get_socket == NULL_PTR))
    {
        /* When using a SocketOwner we need a pointer to function used to
         * create sockets
         */
        return RTI_FALSE;
    }

    if ((OSAPI_System_gv_PortProperty->use_socket_owner == FALSE) &&
        (OSAPI_System_gv_PortProperty->send_data == NULL_PTR))
    {
        /* When not using a SocketOwner we need a pointer to function used to
         * send data
         */
        return RTI_FALSE;
    }

    if (OSAPI_System_gv_PortProperty->use_udp_thread &&
         ((OSAPI_System_gv_PortProperty->number_of_rcv_buffers == 0) ||
          (OSAPI_System_gv_PortProperty->rcv_buffer_size == 0)))
    {
        return RTI_FALSE;
    }

    if (OSAPI_System_gv_PortProperty->max_receive_sockets < 1)
    {
        /* Number of sockets needs to be at least 1
         */
        return RTI_FALSE;
    }

    return TRUE;
}

/*ci
 * \brief Check the consistency of the Autosar port properties.
 *
 * \return TRUE if the Autosar port properties are consistent.
 *         FALSE if the Autosar port properties are not consistent.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_check_properties(void)
{
    if (!OSAPI_SystemAutosar_check_heap_properties())
    {
        return FALSE;
    }

    if (!OSAPI_SystemAutosar_check_mutex_properties())
    {
        return FALSE;
    }

    if (!OSAPI_SystemAutosar_check_semaphore_properties())
    {
        return FALSE;
    }

    if (!OSAPI_SystemAutosar_check_socket_properties())
    {
        return FALSE;
    }

    return TRUE;
}

/*ci \brief Lock the Autosar system mutex.
 *
 *  \return RTI_TRUE if success or RTI_FALSE if error.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_System_lock(void)
{
    return OSAPI_Mutex_take(OSAPI_System_fv_SystemAutosar->mutex);
}

/*ci \brief Unlock the Autosar system mutex.
 *
 *  \return RTI_TRUE if success or RTI_FALSE if error.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_System_unlock(void)
{
    return OSAPI_Mutex_give(OSAPI_System_fv_SystemAutosar->mutex);
}

/*ci \brief Timer handlers implementation.
 */
FUNC(void, SOAD_CODE)
OSAPI_SystemAutosar_handler_callback(void)
{
    RTI_INT32 i, j, event;
    RTI_BOOL bretval;
    P2VAR(struct OSAPI_SystemAutosar, AUTOMATIC, SOAD_APPL_DATA) self =
        OSAPI_System_fv_SystemAutosar;
    RTI_INT32 events = 0;

    if (!self->_parent.is_initialized)
    {
        return;
    }
#ifndef RTI_CERT
    if (self->is_deleted)
    {
        return;
    }
#endif

    if (!OSAPI_System_lock())
    {
        return;
    }

#ifndef RTI_CERT
    /* This is needed in case another task interrupts right before the previous
     * call to OSAPI_System_lock(). In that case the system is already deleted
     * at this point. This is working because the mutex that OSAPI_System_lock()
     * is not actually deleted because Autosar doesn't release memory
     */
    if (self->is_deleted)
    {
        bretval = OSAPI_System_unlock();
        IGNORE_RETVAL(bretval);
        return;
    }
#endif

    if (!OSAPI_Mutex_take(self->tick_mutex))
    {
        bretval = OSAPI_System_unlock();
        IGNORE_RETVAL(bretval);
        return;
    }

    events = self->timer_event_count;
    /* reset the events */
    self->timer_event_count = 0;

    bretval = OSAPI_Mutex_give(self->tick_mutex);
    IGNORE_RETVAL(bretval);

    for (event = 0; event < events; event++)
    {
        for (i = 0, j = self->timer_count; (i < OSAPISYSTEM_MAX_TIMERS) && j; ++i)
        {
            if (self->timer_handler[i].handler)
            {
                j--;
                self->timer_handler[i].handler(self->timer_handler[i].param);
            }
        }
    }

    bretval = OSAPI_System_unlock();
    IGNORE_RETVAL(bretval);
}

/*ci \brief Timer task implementation.
 */
FUNC(void, SOAD_CODE)
OSAPI_SystemAutosar_timer_callback(void)
{
    RTI_UINT32 last_tick_ns;
    RTI_BOOL bretval;
    P2VAR(struct OSAPI_SystemAutosar, AUTOMATIC, SOAD_APPL_DATA) self =
        OSAPI_System_fv_SystemAutosar;

    if (!self->_parent.is_initialized)
    {
        return;
    }
#ifndef RTI_CERT
    if (self->is_deleted)
    {
        return;
    }
#endif

    if (!OSAPI_Mutex_take(self->tick_mutex))
    {
        return;
    }

    last_tick_ns = self->tick_nanosec;

    /* The code in the if branch would be sufficient to handle both case,
     * where timer resolution is greater or equal to 1 second or smaller
     * than 1 second. But in case the resolution is smaller that one second
     * the division to update self->tick_sec is not needed and the / operation
     * might cost some CPU. So this 'if' is an optimization.
     */
    if (OSAPISYSTEM_TIMER_RESOLUTION_NS >= OSAPI_TIME_NSEC_PER_SEC)
    {
        /* Add seconds in the resolution to make sure
         * the remainder is less than 1 sec
         */
        self->tick_sec = self->tick_sec +
               (OSAPISYSTEM_TIMER_RESOLUTION_NS / OSAPI_TIME_NSEC_PER_SEC);

        /* Add the remaining nanoseconds in the resolution to the
         * current nanosec counter, but do not go past 1 sec.
         */
        self->tick_nanosec = (self->tick_nanosec +
             (OSAPISYSTEM_TIMER_RESOLUTION_NS % OSAPI_TIME_NSEC_PER_SEC)) %
                         OSAPI_TIME_NSEC_PER_SEC;
    }
    else
    {
        /* Add the remaining nanoseconds in the resolution to the
         * current nanosec counter, but do not go past 1 sec.
         */
        self->tick_nanosec = (self->tick_nanosec +
                OSAPISYSTEM_TIMER_RESOLUTION_NS) % OSAPI_TIME_NSEC_PER_SEC;
    }

    /* If self->tick_nanosec wrapped around, add 1 more second */
    if (self->tick_nanosec < last_tick_ns)
    {
         self->tick_sec++;
    }

    self->timer_event_count++;

    bretval = OSAPI_Mutex_give(self->tick_mutex);
    IGNORE_RETVAL(bretval);
}

/******************************************************************************
 *  Interface API
 ******************************************************************************/

/*ci \brief Initialize Autosar system.
 *
 * \param[in] self Pointer to Autosar system structure.
 *
 * \return RTI_TRUE if success or already initialized. RTI_FALSE if error.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_initialize(
    P2VAR(struct OSAPI_SystemAutosar, AUTOMATIC, SOAD_APPL_DATA) self)
{
    RTI_INT32 i;

    if (self->_parent.is_initialized)
    {
        return RTI_TRUE;
    }

    /* If properties are not consistent, system can not be initialized */
    if (!OSAPI_SystemAutosar_check_properties())
    {
        return RTI_FALSE;
    }

    for (i = 0; i < OSAPISYSTEM_MAX_TIMERS; ++i)
    {
        self->timer_handler[i].handler = NULL_PTR;
        self->timer_handler[i].param = NULL_PTR;
    }

    self->timer_count = 0;

    self->mutex = OSAPI_Mutex_new();
    if (self->mutex == NULL_PTR)
    {
         return RTI_FALSE;
    }

    self->tick_mutex = OSAPI_Mutex_timer_new();
    if (self->tick_mutex == NULL_PTR)
    {
        return RTI_FALSE;
    }

    self->tick_sec = 0;
    self->tick_nanosec = 0;
    self->timer_event_count = 0;

    self->_parent.is_initialized = RTI_TRUE;
#ifndef RTI_CERT
    self->is_deleted = RTI_FALSE;
#endif

    return RTI_TRUE;
}

#ifndef RTI_CERT
/*ci \brief Finalize Autosar system.
 *
 * \param[in] self Pointer to Autosar system structure.
 *
 * \return RTI_TRUE if success or already finalized. RTI_FALSE if error.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_SystemAutosar_finalize(
    P2VAR(struct OSAPI_SystemAutosar, AUTOMATIC, SOAD_APPL_DATA) self)
{
    RTI_INT32 i;

    if (!self->_parent.is_initialized)
    {
        return RTI_FALSE;
    }

    self->is_deleted = RTI_TRUE;

    if (!OSAPI_System_lock())
    {
        return RTI_FALSE;
    }

    for (i = 0; i < OSAPISYSTEM_MAX_TIMERS; ++i)
    {
        self->timer_handler[i].handler = NULL_PTR;
        self->timer_handler[i].param = NULL_PTR;
    }

    self->timer_count = 0;

    if ((self->tick_mutex != NULL_PTR) && !OSAPI_Mutex_delete(self->tick_mutex))
    {
        return RTI_FALSE;
    }

    if (!OSAPI_System_unlock())
    {
        return RTI_FALSE;
    }

    if ((self->mutex != NULL_PTR) && !OSAPI_Mutex_delete(self->mutex))
    {
        return RTI_FALSE;
    }

    OSAPI_AutosarMutex_finalize();
    OSAPI_AutosarSemaphore_finalize();
    OSAPI_AutosarHeap_finalize();

    self->_parent.is_initialized = RTI_FALSE;

    return RTI_TRUE;
}
#endif /* !RTI_CERT */

/*ci \brief Get current tick time. Output values are meaningful only if
 * RTI_TRUE is returned.
 *
 * \param[out] sec      Current seconds tick value.
 * \param[out] nanosec  Current nanosec tick value.
 *
 * \return RTI_TRUE if success. RTI_FALSE if error.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_get_ticktime(
    P2VAR(RTI_INT32, AUTOMATIC, SOAD_APPL_DATA) sec,
    P2VAR(RTI_UINT32, AUTOMATIC, SOAD_APPL_DATA) nanosec)
{
    if (!OSAPI_Mutex_take(OSAPI_System_fv_SystemAutosar->tick_mutex))
    {
        return RTI_FALSE;
    }

    *sec = OSAPI_System_fv_SystemAutosar->tick_sec;
    *nanosec = OSAPI_System_fv_SystemAutosar->tick_nanosec;

    if (!OSAPI_Mutex_give(OSAPI_System_fv_SystemAutosar->tick_mutex))
    {
        return RTI_FALSE;
    }

    return RTI_TRUE;
}

/*ci \brief Get hostname. Hostname is statically configured during compilation
 * by using OSAPI_PLATFORM_AUTOSAR_HOSTNAME.
 *
 * \param[out] hostname Hostname.
 *
 * \return RTI_TRUE if success. RTI_FALSE if error.
 */
MUST_CHECK_RETURN RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_get_hostname(
    CONSTP2VAR(char, AUTOMATIC, SOAD_APPL_DATA) hostname)
{
    RTI_SIZE_T len;

    len = OSAPI_String_length(OSAPI_PLATFORM_AUTOSAR_HOSTNAME);
    if (len >= OSAPI_SYSTEM_MAX_HOSTNAME)
    {
        len = OSAPI_SYSTEM_MAX_HOSTNAME - 1;
    }
    OSAPI_Memory_copy(hostname, OSAPI_PLATFORM_AUTOSAR_HOSTNAME, len);
    hostname[len] = 0;

    return RTI_TRUE;
}

/*ci \brief Get current time in NTP format. Output value is only meaningful
 * if return value is RTI_TRUE.
 *
 * \param[out] now Current time in Ntp format.
 *
 * \return RTI_TRUE if success. RTI_FALSE if error.
 */
RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_get_time(P2VAR(OSAPI_SystemTime, AUTOMATIC, SOAD_APPL_DATA) now)
{
    RTI_INT32 sec = 0;
    RTI_UINT32 nanosec = 0;

    OSAPI_PRECONDITION(now == NULL_PTR,return RTI_FALSE,
                       OSAPI_Log_entry_add_pointer("now",now,RTI_TRUE);)

    /* There is no standard way to query the current time to Autosar OS.
     * At the moment we rely on EB specific functions but for other
     * implementations we might need to rely on the measured time by the
     * Micro timer task. Even with EB stack, if MicroOs is not loaded it is not
     * possible to translate from ticks to time
     */

    if (OSAPI_System_gv_System->is_initialized)
    {
        if (!OSAPI_AutosarSystem_get_ticktime(&sec, &nanosec))
        {
            return RTI_FALSE;
        }
    }

    now->sec  = sec;
    now->nanosec = nanosec;

    return RTI_TRUE;
}

/*ci \brief Start a new timer.
 *
 * \param[in] self         Timer to start.
 * \param[in] tick_handler Timer handler function.
 *
 * \return RTI_TRUE if success. RTI_FALSE if error.
 */
RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_start_timer(OSAPI_Timer_T self,
                                OSAPI_TimerTickHandlerFunction tick_handler)
{
    uint32 i;

    OSAPI_PRECONDITION((self == NULL_PTR) || (tick_handler == NULL_PTR),
            return RTI_FALSE,
            OSAPI_Log_entry_add_pointer("self",self,RTI_FALSE);
            OSAPI_Log_entry_add_pointer("tick_handler",tick_handler,RTI_TRUE);)

    if (!OSAPI_SystemAutosar_initialize(OSAPI_System_fv_SystemAutosar))
    {
        OSAPI_LOG_SYSTEM_TIMER_START(OSAPI_LOGKIND_ERROR)
        return RTI_FALSE;
    }

    if (!OSAPI_System_lock())
    {
        OSAPI_LOG_SYSTEM_TIMER_START(OSAPI_LOGKIND_ERROR)
        return RTI_FALSE;
    }

    if (OSAPI_System_fv_SystemAutosar->timer_count == OSAPISYSTEM_MAX_TIMERS)
    {
        OSAPI_LOG_SYSTEM_TIMER_START(OSAPI_LOGKIND_ERROR)
        (void)OSAPI_System_unlock();
        return RTI_FALSE;
    }

    for (i = 0; i < OSAPISYSTEM_MAX_TIMERS; ++i)
    {
        if (OSAPI_System_fv_SystemAutosar->timer_handler[i].handler == NULL_PTR)
        {
            break;
        }
    }

    if (i == OSAPISYSTEM_MAX_TIMERS)
    {
        OSAPI_LOG_SYSTEM_TIMER_START(OSAPI_LOGKIND_ERROR)
        (void)OSAPI_System_unlock();
        return RTI_FALSE;
    }

    OSAPI_System_fv_SystemAutosar->timer_handler[i].handler = tick_handler;
    OSAPI_System_fv_SystemAutosar->timer_handler[i].param = self;
    ++OSAPI_System_fv_SystemAutosar->timer_count;

    return OSAPI_System_unlock();
}

#ifndef RTI_CERT
/*ci \brief Stop a running timer.
 *
 * \param[in] self         Timer to stop.
 *
 * \return RTI_TRUE if success. RTI_FALSE if error.
 */
RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_stop_timer(OSAPI_Timer_T self)
{
    uint32 i;

    OSAPI_PRECONDITION((self == NULL_PTR),
                       return RTI_FALSE,
                       OSAPI_Log_entry_add_pointer("self",self,RTI_TRUE);)

    if (!OSAPI_System_fv_SystemAutosar->_parent.is_initialized)
    {
        OSAPI_LOG_SYSTEM_TIMER_STOP(OSAPI_LOGKIND_ERROR)
        return RTI_FALSE;
    }

    if (!OSAPI_System_lock())
    {
        OSAPI_LOG_SYSTEM_TIMER_STOP(OSAPI_LOGKIND_ERROR)
        return RTI_FALSE;
    }

    for (i = 0; i < OSAPISYSTEM_MAX_TIMERS; ++i)
    {
        if (OSAPI_System_fv_SystemAutosar->timer_handler[i].param == self)
        {
            OSAPI_System_fv_SystemAutosar->timer_handler[i].handler = NULL_PTR;
            OSAPI_System_fv_SystemAutosar->timer_handler[i].param = NULL_PTR;
            --OSAPI_System_fv_SystemAutosar->timer_count;
        }
    }

    if (!OSAPI_System_unlock())
    {
        OSAPI_LOG_SYSTEM_TIMER_STOP(OSAPI_LOGKIND_ERROR)
        return RTI_FALSE;
    }

    return RTI_TRUE;
}
#endif

/*ci \brief Get Autosar system timer resolution.
 *
 * \return Autosar system timer resolution in nanoseconds, or 0 if
 * system is not initialized and initialization fails.
 */
RTI_PRIVATE FUNC(RTI_INT32, SOAD_CODE)
OSAPI_AutosarSystem_get_timer_resolution(void)
{
    if (!OSAPI_SystemAutosar_initialize(OSAPI_System_fv_SystemAutosar))
    {
        OSAPI_LOG_SYSTEM_TIMER_START(OSAPI_LOGKIND_ERROR)
        return 0;
    }

    return OSAPISYSTEM_TIMER_RESOLUTION_NS;
}

RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_initialize(void)
{
    return OSAPI_SystemAutosar_initialize(OSAPI_System_fv_SystemAutosar);
}

#ifndef RTI_CERT
RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_finalize(void)
{
    return OSAPI_SystemAutosar_finalize(OSAPI_System_fv_SystemAutosar);
}
#endif

/*ci \brief Get IP address. This can be used to generate unique identifiers.
 * Output value is meaningful only if return value is RTI_TRUE.
 *
 * \param[out] address      IP address.
 *
 * \return RTI_TRUE if success or RTI_FALSE if error.
 */
RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_get_ip_address(
    P2VAR(RTI_UINT32, AUTOMATIC, SOAD_APPL_DATA) address)
{
    TcpIp_LocalAddrIdType idx = 0;
    uint32 ipVxAddrBuffer[2][8] = {{0}};
    uint8 netmask;

    RTI_BOOL ret_value = RTI_FALSE;

    for (idx = 0; idx <= OSAPI_System_gv_PortProperty->max_local_addr_id; idx++)
    {
        ((TcpIp_SockAddrType *)&ipVxAddrBuffer[0])->DOMAIN_FIELD = TCPIP_AF_INET;
        ((TcpIp_SockAddrType *)&ipVxAddrBuffer[1])->DOMAIN_FIELD = TCPIP_AF_INET;

        if (TcpIp_GetIpAddr(
                idx,
                (TcpIp_SockAddrType *)&ipVxAddrBuffer[0],
                &netmask,
                (TcpIp_SockAddrType *)&ipVxAddrBuffer[1]) == E_OK)
        {
            if ((((TcpIp_SockAddrType *)&ipVxAddrBuffer[0])->DOMAIN_FIELD == TCPIP_AF_INET)
                && (((TcpIp_SockAddrInetType *)&ipVxAddrBuffer[0])->addr[0] != 0))
            {
                *address = ((TcpIp_SockAddrInetType *)&ipVxAddrBuffer[0])->addr[0];
                ret_value = RTI_TRUE;
            }
        }
    }

    return ret_value;
}

/*ci \brief Generate a unique identifier.
 * Output value is meaningful only if return value is RTI_TRUE.
 *
 * \param[out] uuid_out    Unique identifier.
 *
 * \return RTI_TRUE if success or RTI_FALSE if error.
 */
RTI_PRIVATE FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_AutosarSystem_generate_uuid(
    P2VAR(struct OSAPI_SystemUUID, AUTOMATIC, SOAD_APPL_DATA) uuid_out)
{
    OSAPI_SystemTime now;
    RTI_UINT32 address;
    OSAPI_ThreadId thread_id;

    OSAPI_PRECONDITION((uuid_out == NULL_PTR),
                       return RTI_FALSE,
                       OSAPI_Log_entry_add_pointer("uuid_out",uuid_out,RTI_TRUE);)

    if (!OSAPI_System_get_time(&now))
    {
        return RTI_FALSE;
    }

    /* It is considered unlikely that OSAPI_System_fv_UuidCounter will overflow.
     * The OSAPI_System_fv_UuidCounter is limited by the max_participant
     * resource-limit and the hard-coded limit of 8 participants
     * (OSAPISYSTEM_MAX_TIMERS) documented in "Connext DDS Micro Hardcoded
     * Resource Limits" in the User's Manual. When compiled with RTI_CERT,
     * it is not possible to delete entities, and thus
     * OSAPI_System_fv_UuidCounter cannot overflow. For
     * non-RTI_CERT system it is unlikely that an overflow will happen since
     * memory is never freed and with a possible 559038241 create/delete
     * cycles, a 10KB application will need 5590382410 = 5.6TB of total memory
     * and it is safe to assume the autosar system will run out of memory
     * before OSAPI_System_fv_UuidCounter overflows.
     */
#if RTI_ENDIAN_LITTLE
    uuid_out->value[0] = ((OSAPI_System_fv_UuidCounter&0xff000000U)>>24) |
                         ((OSAPI_System_fv_UuidCounter&0x00ff0000U)>>8)  |
                         ((OSAPI_System_fv_UuidCounter&0x000000ffU)<<24) |
                         ((OSAPI_System_fv_UuidCounter&0x0000ff00U)<<8);
    OSAPI_System_fv_UuidCounter++;
#else
    uuid_out->value[0] = OSAPI_System_fv_UuidCounter++;
#endif
    if (OSAPI_AutosarSystem_get_ip_address(&address))
    {
        uuid_out->value[1] = address;
    }
    else
    {
        thread_id = OSAPI_Thread_self();
        uuid_out->value[1] = (RTI_UINT32)thread_id.handle.handle32;
    }
    uuid_out->value[2] = (RTI_UINT32)now.nanosec;
    uuid_out->value[3] = (RTI_UINT32)now.sec;

    return RTI_TRUE;
}

FUNC(void, SOAD_CODE)
OSAPI_System_get_native_interface(
    P2VAR(struct OSAPI_SystemI, AUTOMATIC, SOAD_APPL_DATA) intf)
{
    OSAPI_PRECONDITION_ALWAYS(intf == NULL,
                           return,
                           OSAPI_Log_entry_add_pointer("intf",intf,RTI_TRUE);)

    intf->start_timer = OSAPI_AutosarSystem_start_timer;
#ifndef RTI_CERT
    intf->stop_timer = OSAPI_AutosarSystem_stop_timer;
#endif
    intf->get_timer_resolution = OSAPI_AutosarSystem_get_timer_resolution;
    intf->get_time = OSAPI_AutosarSystem_get_time;
    intf->initialize = OSAPI_AutosarSystem_initialize;
#ifndef RTI_CERT
    intf->finalize = OSAPI_AutosarSystem_finalize;
#endif /* !RTI_CERT */
    intf->generate_uuid = OSAPI_AutosarSystem_generate_uuid;
    intf->get_hostname = OSAPI_AutosarSystem_get_hostname;
    intf->get_ticktime = OSAPI_AutosarSystem_get_ticktime;
}

FUNC(RTI_BOOL, SOAD_CODE)
OSPSL_AutosarSystem_get_property(struct OSAPI_SystemAutosar *property)
{
    RTI_BOOL result;

    *property = *OSAPI_System_fv_SystemAutosar;
    result = OSAPI_System_get_property(&property->_parent.property);

    return result;
}

FUNC(RTI_BOOL, SOAD_CODE)
OSPSL_AutosarSystem_set_property(struct OSAPI_SystemAutosar *property)
{
    RTI_BOOL result;

    result = OSAPI_System_set_property(&property->_parent.property);
    *OSAPI_System_fv_SystemAutosar = *property;

    return result;
}
