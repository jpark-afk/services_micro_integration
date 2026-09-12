/*
 * FILE: autosarMutex.c - AutoSAR mutex functionality
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
 * 6oct2020,fmt MICRO-2585/PR.28155
 *   - Move consistency check of properties from
 *     OSAPI_AutosarMutex_is_initialized() to
 *     OSAPI_SystemAutosar_initialize()
 * 21may2020,fmt MICRO-2409/PR.27650 Exclude from cert build finalize() functions
 * 21may2020,fmt MICRO-2405/PR.27629 Simplify Autosar initialize() functions
 * 13mar2019,fmt Written
 *
 */
/*ce
 * \file
 * \brief AutoSAR implementation of OSAPI mutex routines
 */
#include "autosarMutex.h"

/* workaround#COMMON - task overrun issue */
#include "dds_cdd_adapter.h"
extern DdsCdd_InitState_t dds_cdd_init_state;

/* Global mutex lock */
RTI_PRIVATE struct OSAPI_Mutex OSAPI_AutosarMutex_fv_GlobalMutex = OSAPI_MUTEX_INITIALIZER;

/* Timer mutex lock */
RTI_PRIVATE struct OSAPI_Mutex OSAPI_AutosarMutex_fv_TimerMutex = OSAPI_MUTEX_INITIALIZER;

/* Netio mutex lock */
RTI_PRIVATE struct OSAPI_Mutex OSAPI_AutosarMutex_fv_NetioMutex = OSAPI_MUTEX_INITIALIZER;



/*ci \brief Whether the Autosar mutexes have been initialized or not
 */
RTI_PRIVATE RTI_BOOL OSAPI_AutosarMutex_fv_IsInitialized = RTI_FALSE;

/*** SOURCE_BEGIN ***/

/* OSAPI autosar module private functions */

/*ci \brief Checks if the mutex is owned by the current thread.
 *
 *  \param[in] mutex Mutex to check for ownership.
 *
 *  \return TRUE if the mutex is owned by the current thread. Otherwise FALSE.
 */
RTI_PRIVATE FUNC(boolean, SOAD_CODE)
OSAPI_Mutex_is_owned(struct OSAPI_Mutex *mutex)
{
    OSAPI_ThreadId thread_self = OSAPI_Thread_self();

    return (mutex->owned &&
            (mutex->_base.owner.handle.handle32 == thread_self.handle.handle32)) ? TRUE : FALSE;
}

/*ci \brief Ensures that Autosar mutex module is initialized.
 *
 *  \return TRUE if module is initialized with no error or already initialized.
 *          Otherwise FALSE.
 */
RTI_PRIVATE FUNC(boolean, SOAD_CODE)
OSAPI_AutosarMutex_is_initialized(void)
{
    if (OSAPI_AutosarMutex_fv_IsInitialized)
    {
        return TRUE;
    }

    /* Initialize the Global Mutex Data ONCE */
    OSAPI_Memory_zero(&OSAPI_AutosarMutex_fv_GlobalMutex, sizeof(struct OSAPI_Mutex));
    
    /* Assign the specific OS Resource ID to it. 
     * We use the first configured resource ID as the single global lock. 
     */
    OSAPI_AutosarMutex_fv_GlobalMutex.hmutex = OSAPI_System_gv_PortProperty->mutex_resource_id;

    OSAPI_AutosarMutex_fv_IsInitialized = RTI_TRUE;

    return TRUE;
}

/* OSAPI autosar module public functions */

#ifndef RTI_CERT
FUNC(void, SOAD_CODE)
OSAPI_AutosarMutex_finalize(void)
{
    /* set global variables to their default values */

    OSAPI_AutosarMutex_fv_IsInitialized = RTI_FALSE;
}
#endif

FUNC(StatusType, SOAD_CODE)
OSAPI_AutosarMutex_enter_critical_section(ResourceType resource)
{
    StatusType stat;

    switch (OSAPI_System_gv_PortProperty->sync_type)
    {
        case OSAPI_AUTOSAR_SYNCKIND_RESOURCES:
            stat = GetResource(resource);
            break;
        
#if RTIME_AUTOSAR_SPINLOCK_ENABLED
        case OSAPI_AUTOSAR_SYNCKIND_SPINLOCK:
            stat = GetSpinlock(OSAPI_System_gv_PortProperty->spinlock_id);
            break;
#endif /* RTIME_AUTOSAR_SPINLOCK_ENABLED */

        default:
            stat = E_NOT_OK;
            break;
    }
    
    return stat;
}

FUNC(StatusType, SOAD_CODE)
OSAPI_AutosarMutex_leave_critical_section(ResourceType resource)
{
    StatusType stat;

    switch (OSAPI_System_gv_PortProperty->sync_type)
    {
        case OSAPI_AUTOSAR_SYNCKIND_RESOURCES:
            stat = ReleaseResource(resource);
            break;
        
#if RTIME_AUTOSAR_SPINLOCK_ENABLED
        case OSAPI_AUTOSAR_SYNCKIND_SPINLOCK:
            stat = ReleaseSpinlock(OSAPI_System_gv_PortProperty->spinlock_id);
            break;
#endif /* RTIME_AUTOSAR_SPINLOCK_ENABLED */
            
        default:
            stat = E_NOT_OK;
            break;
    }
    
    return stat;
}

/* OSAPI public functions */

#ifndef RTI_CERT
FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_Mutex_delete(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA) mutex)
{
    OSAPI_PRECONDITION(mutex == NULL_PTR,return RTI_FALSE,
                       OSAPI_Log_entry_add_pointer("mutex",mutex,RTI_TRUE);)

    /* 
     * Since we are using a singleton global mutex shared by all tasks,
     * we CANNOT free or zero-out the memory here, as other tasks may
     * still be using it or waiting on it.
     */
     
    return RTI_TRUE;
}
#endif

FUNC(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA), SOAD_CODE)
OSAPI_AutosarMutex_initialize_mutex(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA) mutex)
{
    if (!OSAPI_AutosarMutex_is_initialized())
    {
        OSAPI_LOG_MUTEX_NEW(OSAPI_LOGKIND_ERROR)
        return NULL_PTR;
    }

    /* If this is the global mutex, it was already initialized in is_initialized().
     * We should not wipe it out here, as it may be in use.
     */
    if (mutex == &OSAPI_AutosarMutex_fv_GlobalMutex)
    {
        return mutex;
    }

    /* Fallback for external structs: just clear and assign resource ID */
    OSAPI_Memory_zero(mutex, sizeof(struct OSAPI_Mutex));
    mutex->hmutex = OSAPI_System_gv_PortProperty->mutex_resource_id;

    return mutex;
}

FUNC(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA), SOAD_CODE)
OSAPI_Mutex_new(void)
{
    if (!OSAPI_AutosarMutex_is_initialized())
    {
        OSAPI_LOG_MUTEX_NEW(OSAPI_LOGKIND_ERROR)
        return NULL_PTR;
    }
    
    /* Always return the SINGLETON global mutex. 
     * Do not allocate new memory. 
     */
    return &OSAPI_AutosarMutex_fv_GlobalMutex;
}

FUNC(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA), SOAD_CODE)
OSAPI_Mutex_timer_new(void)
{
    /* Initialize the Timer Mutex Data ONCE */
    OSAPI_Memory_zero(&OSAPI_AutosarMutex_fv_TimerMutex, sizeof(struct OSAPI_Mutex));
    
    /* Assign the specific OS Resource ID to it */
    OSAPI_AutosarMutex_fv_TimerMutex.hmutex = OSAPI_System_gv_PortProperty->timer_resource_id;

    return &OSAPI_AutosarMutex_fv_TimerMutex;
}

FUNC(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA), SOAD_CODE)
OSAPI_Mutex_netio_new(void)
{
    /* Initialize the Netio Mutex Data ONCE */
    OSAPI_Memory_zero(&OSAPI_AutosarMutex_fv_NetioMutex, sizeof(struct OSAPI_Mutex));
    
    /* Assign the specific OS Resource ID to it */
    OSAPI_AutosarMutex_fv_NetioMutex.hmutex = OSAPI_System_gv_PortProperty->netio_resource_id;

    return &OSAPI_AutosarMutex_fv_NetioMutex;
}

FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_Mutex_take(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA) mutex)
{
    StatusType ret_value;
    RTI_BOOL success = RTI_FALSE;
    /* workaround#COMMON - task overrun issue */
    OSAPI_ThreadId self; //= OSAPI_Thread_self();

    OSAPI_PRECONDITION(mutex == NULL_PTR,return RTI_FALSE,
                       OSAPI_Log_entry_add_pointer("mutex",mutex,RTI_TRUE);)

    /* workaround#COMMON - task overrun issue */
    if (dds_cdd_init_state < DdsCdd_InitState_EntitiesCreated) return RTI_TRUE;   
    self = OSAPI_Thread_self();

    /* check recursion using internal state of the singleton */
    if (OSAPI_Mutex_is_owned(mutex))
    {
        /* thread already owns the lock */
        mutex->depth++;
        success = RTI_TRUE;
    }
    else
    {
        /* thread does not own the lock, we get the resource */
        /* Use the mutex's stored resource ID */
        ret_value = OSAPI_AutosarMutex_enter_critical_section(mutex->hmutex);
        
        if (ret_value == E_OK)
        {
            mutex->owned = RTI_TRUE;
            mutex->_base.owner = self;
            mutex->depth = 1;
            
            success = RTI_TRUE;
        }
        else
        {
            OSAPI_LOG_MUTEX_TAKE(OSAPI_LOGKIND_ERROR, ret_value)
            success = RTI_FALSE;
        }
    }

    if (success)
    {
        RTI_OS_DSYNC();
    }
    
    return success;
}

FUNC(RTI_BOOL, SOAD_CODE)
OSAPI_Mutex_give(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA) mutex)
{
    StatusType ret_value;
    RTI_BOOL success = RTI_FALSE;

    OSAPI_PRECONDITION(mutex == NULL_PTR,return RTI_FALSE,
                       OSAPI_Log_entry_add_pointer("mutex",mutex,RTI_TRUE);)

    /* workaround#COMMON - task overrun issue */
    if (dds_cdd_init_state < DdsCdd_InitState_EntitiesCreated) return RTI_TRUE;

    if (!OSAPI_Mutex_is_owned(mutex))
    {
        return RTI_FALSE;
    }

    --mutex->depth;

    if (mutex->depth > 0)
    {
        RTI_OS_DSYNC();
        return RTI_TRUE;
    }

    mutex->owned = RTI_FALSE;
    RTI_OS_DSYNC();

    /* last release of the nested mutex, release the resource*/
    
    ret_value = OSAPI_AutosarMutex_leave_critical_section(mutex->hmutex);
    
    if (ret_value == E_OK)
    {
        success = RTI_TRUE;
    }
    else
    {
        OSAPI_LOG_MUTEX_GIVE(OSAPI_LOGKIND_ERROR, ret_value)
        success = RTI_FALSE;
    }

    return success;
}

FUNC(RTI_UINT32, SOAD_CODE)
OSAPI_Mutex_get_depth(P2VAR(struct OSAPI_Mutex, AUTOMATIC, SOAD_APPL_DATA) self)
{
    OSAPI_PRECONDITION(self == NULL,return RTI_FALSE,
                            OSAPI_Log_entry_add_pointer("self",self,RTI_TRUE);)
    return self->depth;
}
