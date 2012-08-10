// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_TCPADDRESS_H
#define CONVEYOR_TCPADDRESS_H (1)

#include <string>

#include <conveyor/fwd.h>
#include <conveyor/address.h>

namespace conveyor
{
    class TcpAddress : public Address
    {
    public:
        TcpAddress (std::string const & host, int port);

        Connection * createConnection (void) const;
        std::string const & host (void) const;
        int port (void) const;

    private:
        std::string const m_host;
        int const m_port;
    };
}

#endif
