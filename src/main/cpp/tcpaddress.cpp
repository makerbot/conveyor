// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstring>
#include <exception>
#include <string>
#include <sys/types.h>

#ifdef _WIN32
# include <winsock2.h>
# include <ws2tcpip.h>
#else
# include <netinet/in.h>
# include <netdb.h>
# include <sys/socket.h>
#endif

#include <conveyor/address.h>
#include <conveyor/connection.h>
#include <conveyor/tcpaddress.h>

#include "socketconnectionprivate.h"

namespace conveyor
{
    TcpAddress::TcpAddress (std::string const & host, int port)
        : m_host (host)
        , m_port (port)
    {
    }

    Connection *
    TcpAddress::createConnection (void) const
    {
        SocketConnectionPrivate::socket_t const fd (socket (PF_INET, SOCK_STREAM, IPPROTO_TCP));
        if (invalidSocket(fd))
        {
            throw std::exception ();
        }
        else
        {
            struct sockaddr_in address;
            memset (& address, 0, sizeof (struct sockaddr_in));
            address.sin_family = AF_INET;
            address.sin_port = htons (this->m_port);
            struct hostent * host;
            host = gethostbyname (this->m_host.c_str ());
            if (0 == host)
            {
                throw std::exception ();
            }
            else
            {
                std::memcpy
                    ( & address.sin_addr.s_addr
                    , host->h_addr_list[0]
                    , host->h_length
                    );
                if (0 != connect
                    ( fd
                    , reinterpret_cast <struct sockaddr *> (& address)
                    , sizeof (struct sockaddr_in)
                    ))
                {
                    throw std::exception ();
                }
                else
                {
                    ConnectionPrivate * const private_
                        ( new SocketConnectionPrivate (fd)
                        );
                    Connection * const connection (new Connection (private_));
                    return connection;
                }
            }
        }
    }

    std::string const &
    TcpAddress::host (void) const
    {
        return this->m_host;
    }

    int
    TcpAddress::port (void) const
    {
        return this->m_port;
    }
}
