// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <string>

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
        SocketConnectionPrivate * const private_
            ( SocketConnectionPrivate::connectTcp
                ( this->m_host
                , this->m_port
                )
            );
        Connection * const connection (new Connection (private_));
        return connection;
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
