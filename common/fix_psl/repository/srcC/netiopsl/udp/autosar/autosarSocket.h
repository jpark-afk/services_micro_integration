/*
 * FILE: autosarSocket.h - Autosar socket functionality
 *
 * Copyright 2012-2026 Real-Time Innovations, Inc.
 *
 * All rights reserved.
 *
 * No duplications, whole or partial, manual or electronic, may be made
 * without express written permission. Any such copies, or
 * revisions thereof, must display this notice unaltered.
 * This code contains trade secrets of Real-Time Innovations, Inc.
 *
 * Modification History
 * --------------------
 * 21jul2021,tk MICRO-3045 Fixed filenames and dates in file header comments
 * 26nov2020,fmt MICRO-2666/PR.28290
 *    - Fix description of return value in documentation of function
 *      NETIO_AutosarSocket_sendto().
 * 26nov2020,fmt MICRO-2665/PR.28285
 *    - Fix parameter description of function NETIO_AutosarSocket_recvnotify().
 * 21may2020,fmt MICRO-2409/PR.27650 Exclude from cert build finalize() functions
 * 11apr2019,fmt File created
 *
 */
/*ce
 * \file
 */

#ifndef autosarSocket_h
#define autosarSocket_h


#ifndef rti_me_psl_dll_h
#include "rti_me_psl/rti_me_psl_dll.h"
#endif

#include "rti_me_psl.h"

#ifndef netio_config_h
#include "netio/netio_config.h"
#endif

#ifndef netio_interface_h
#include "netio/netio_interface.h"
#endif

#ifndef osapi_types_h
#include "osapi/osapi_types.h"
#endif

#ifndef osapi_string_h
#include "osapi/osapi_string.h"
#endif

#ifndef osapi_heap_h
#include "osapi/osapi_heap.h"
#endif

#ifndef osapi_thread_h
#include "osapi/osapi_thread.h"
#endif

#ifndef reda_string_h
#include "reda/reda_string.h"
#endif

#ifndef db_api_h
#include "db/db_api.h"
#endif

#ifndef rt_rt_h
#include "rt/rt_rt.h"
#endif

#ifndef netio_log_h
#include "netio/netio_log.h"
#endif

#ifndef netio_common_h
#include "netio/netio_common.h"
#endif

#ifndef netio_address_h
#include "netio/netio_address.h"
#endif

#ifndef netio_route_h
#include "netio/netio_route.h"
#endif

#ifndef netio_udp_h
#include "netio/netio_udp.h"
#endif

#if !UDP_EXCLUDE_BUILTIN


/*ci \brief The maximum allowed payload in a UDP packet. While the UDP header
 *    has a 16-bit length field, this includes the UDP header and IP headers
 *    as well. Thus, 65507 bytes is the maximum number of bytes that can be
 *    sent. Note that this does not take into account any IP or UDP header
 *    extensions is the best case scenario.
 */
#define UDP_MAX_PACKET_LENGTH 8192

/*ci \brief Size for the local address ID bitmap. This is the maximum number 
 *    of local addresses that can be configured.
 */
#define MAX_LOCAL_ADDR_IDS 32
/*i
 *
 * \brief Length opaque type
 */
typedef unsigned int socklen_t;

/*i
 *
 * \brief IP address in network byte order
 */
struct in_addr 
{
    unsigned long s_addr;
};

/*i
 *
 * \brief Socket address. Defined as a combination of an IP interface
 * address and a 16-bit port number.
 */
struct sockaddr_in 
{
    /*i
     *
     * \brief Address family: AF_INET
     */
    short sin_family;

    /*i
     *
     * \brief Port
     */
    unsigned short sin_port;

    /*i
     *
     * \brief Internet address
     */
    struct in_addr sin_addr;

    /*i
     *
     * \brief Zero. Padding.
     */
    char sin_zero[8];
};

/*i
 *
 * \brief Used to define a socket address which is used in the
 * NETIO_AutosarSocket_bind(), NETIO_AutosarSocket_recvfrom() and
 * NETIO_AutosarSocket_sendto() functions.
 */
struct sockaddr 
{
    /*i
     *
     * \brief Address family, AF_xxx
     */
    unsigned short sa_family;

    /*i
     *
     * \brief 14 bytes of protocol address
     */
    char sa_data[14];
};

/*i
 *
 * \brief Provides multicast group information for IPv4 addresses.
 */
struct ip_mreq
{
    /*i
     *
     * \brief IP multicast group address.
     */
    struct in_addr imr_multiaddr;

    /*i
     *
     * \brief IP address of local interface.
     */
    struct in_addr imr_interface;

    /*i
     *
     * \brief IP address of multicast source.
     */
    struct in_addr imr_sourceaddr;
};

struct iovec
{
    void  *iov_base;              /* Starting address */
    size_t iov_len;               /* Number of bytes to transfer */
};

struct msghdr
{
    void         *msg_name;       /* optional address */
    socklen_t     msg_namelen;    /* size of address */
    struct iovec *msg_iov;        /* scatter/gather array */
    size_t        msg_iovlen;     /* # elements in msg_iov */
    void         *msg_control;    /* ancillary data, see below */
    size_t        msg_controllen; /* ancillary data buffer len */
    int           msg_flags;      /* flags on received message */
};

#ifndef SOCK_DGRAM
#define SOCK_DGRAM 0
#endif
#ifndef AF_INET
#define AF_INET    0
#endif
#ifndef INADDR_ANY
#define INADDR_ANY 0
#endif

#ifndef IPPROTO_IP
#define IPPROTO_IP  0
#endif
#ifndef SOL_SOCKET
#define SOL_SOCKET  1
#endif

#if NETIO_CONFIG_ENABLE_MULTICAST
#ifndef IP_MULTICAST_LOOP
#define IP_MULTICAST_LOOP  1
#endif
#ifndef IP_MULTICAST_IF
#define IP_MULTICAST_IF    2
#endif
#ifndef IP_MULTICAST_TTL
#define IP_MULTICAST_TTL   3
#endif
#ifndef IP_ADD_MEMBERSHIP
#define IP_ADD_MEMBERSHIP  4
#endif
#ifndef IP_DROP_MEMBERSHIP
#define IP_DROP_MEMBERSHIP 5
#endif
#endif /* NETIO_CONFIG_ENABLE_MULTICAST */

#ifndef SO_SNDBUF
#define SO_SNDBUF          6
#endif
#ifndef SO_RCVBUF
#define SO_RCVBUF          7
#endif
#ifndef SO_REUSEPORT
#define SO_REUSEPORT       8
#endif
#ifndef SO_REUSEADDR
#define SO_REUSEADDR       9
#endif

#ifndef EADDRINUSE
#define EADDRINUSE 1
#endif

/*i
 * \brief Return value used by some functions to indicate error.
 */
#define SOCKET_ERROR ((int)-1)

/*ci
 * \brief Function to initialize AutoSAR NETIO
 *
 * \return RTI_TRUE if success. RTI_FALSE in case of error.
 */
MUST_CHECK_RETURN NETIODllExport FUNC(RTI_BOOL, SOAD_CODE)
NETIO_Autosar_initialize(void);

#ifndef RTI_CERT
/*ci
 * \brief Function to finalize AutoSAR NETIO
 */
NETIODllExport FUNC(void, SOAD_CODE)
NETIO_Autosar_finalize(void);

#endif /* !RTI_CERT */

/*ci 
 * \brief Callback function that can process an incoming UDP packet. This
 * callback is used by sockets which have a notification callback.
 *
 * \param[in] user_data Port entry associated with the socket where the packets
 *                      has been received.
 * \param[in] buffer Pointer to received data
 * \param[in] rx_len Length of data buffer
 * \param[in] ip_src Source IP address and port
 */
typedef void (*NETIO_AutosarSocket_interface_receive)(
    void *user_data,
    char *buffer,
    RTI_INT32 rx_len,
    const struct sockaddr_in *ip_src);

/*ci 
 * \brief Creates a new socket.
 *
 * \param [in] protocol_family The only supported value is AF_INET
 * \param [in] type The only supported value is SOCK_DGRAM
 * \param [in] protocol The only supported value is IPPROTO_IP
 *
 * \return SOCKET_ERROR if error, otherwise a valid socket id
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_socket(int protocol_family, int type, int protocol);

/*ci 
 * \brief Deletes a previously created socket.
 *
 * \param [in] socket Socket to close.
 *
 * \return SOCKET_ERROR if error, otherwise 0
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_close(int socket);

/*ci 
 * \brief Binds a socket to a port.
 *
 * \param [in] socket Socket to bind.
 * \param [in] addr Port to bind socket to.
 * \param [in] addr_len Size of parameter addr.
 *
 * \return SOCKET_ERROR if error, otherwise 0
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_bind(int socket,
                         P2CONST(struct sockaddr, AUTOMATIC, SOAD_APPL_DATA) addr, 
                         socklen_t addr_len);
/*ci
 * \brief Returns the localAddrId configured with the provided address
 *
 * \param[in] addr Pointer to the address to be found.
 * \param[out] local_addr_id Pointer to the localAddrId to be retrieved
 *
 * \return E_OK if localAddrId is found and returned.
 * E_NOT_OK otherwise.
 */
extern FUNC(Std_ReturnType, SOAD_CODE) NETIO_AutosarSocket_find_local_addr_id(
    P2CONST(struct sockaddr, AUTOMATIC, SOAD_APPL_DATA) addr,
    TcpIp_LocalAddrIdType *local_addr_id);

/*ci
 * \brief MICRO-12928: Bind a send socket to an ephemeral port on the
 *        configured send_local_addr_id.
 *
 * Always requests TCPIP_PORT_ANY.  Called at init and during recovery.
 *
 * \param[in] socket  Socket ID.
 *
 * \return 0 on success, SOCKET_ERROR on failure.
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_bind_send(int * socket, TcpIp_LocalAddrIdType expected_local_addr_id);

/*ci 
 * \brief Sets a callback function that will be called when new data is
 *        received in the socket.
 *
 * \param [in] socket Socket to receive data from.
 * \param [in] udp_queue Callback function that will be called when a new packet
 *                       is available in the socket.
 * \param [in] user_data User data to use when a new packet is available
 *                       in the socket.
 *
 * \return SOCKET_ERROR if error, otherwise 0
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_recvnotify(
    int socket, 
    NETIO_AutosarSocket_interface_receive udp_queue,
    P2VAR(void, AUTOMATIC, SOAD_APPL_DATA) user_data);

/*ci 
 * \brief Sends data using a socket.
 *
 * \param [in] socket Socket to receive data from.
 * \param [in] msg Pointer to data to send. 
 * \param [in] msg_len Size of data to send.
 * \param [in] flags Not used.
 * \param [in] dest_addr Destination address and port.
 * \param [in] addr_len Size of parameter dest_addr.
 *
 *  \return On success, this call return the number of characters sent.
 *          On error, SOCKET_ERROR is returned. 
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_sendto(
    int socket, 
    P2VAR(void, AUTOMATIC, SOAD_APPL_DATA) msg, 
    int msg_len, int flags,
    P2CONST(struct sockaddr, AUTOMATIC, SOAD_APPL_DATA) dest_addr, 
    socklen_t addr_len);


extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_sendmsg(
    int socket,
    P2CONST(struct msghdr, AUTOMATIC, SOAD_APPL_DATA) msg,
    int flags);

/*ci 
 * \brief Sets socket options. AutoSAR socket don't support any of the options
 * set by \rtime but this function returns an error only if the option passed as
 * parameter is not one of the options set by \rtime.
 *
 * \param [in] socket Socket id.
 * \param [in] level Only IPPROTO_IP and SOL_SOCKET are supported. 
 * \param [in] opt_name Option name.
 * \param [in] opt_val Option value.
 * \param [in] opt_len Option value length.
 *
 * \return SOCKET_ERROR if error, otherwise 0
 */
extern FUNC(int, SOAD_CODE)
NETIO_AutosarSocket_setsockopt(int socket, int level, int opt_name,
                               P2CONST(void, AUTOMATIC, SOAD_APPL_DATA) opt_val,
                               socklen_t opt_len);

#endif /* !UDP_EXCLUDE_BUILTIN */

#endif  /* autosarSocket_h */
