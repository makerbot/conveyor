// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstring>
#include <exception>
#include <string>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>

#include <conveyor/address.h>
#include <conveyor/unixaddress.h>

#include "socketconnectionprivate.h"

namespace conveyor
{
    UnixAddress::UnixAddress (std::string const & path)
        : m_path (path)
    {
    }

    Connection *
    UnixAddress::createConnection (void) const
    {
        int const fd (socket (PF_UNIX, SOCK_STREAM, 0));
        if (fd < 0)
        {
            throw std::exception ();
        }
        else
        {
            struct sockaddr_un address;
            memset (& address, 0, sizeof (struct sockaddr_un));
            address.sun_family = AF_UNIX;
            char const * const path (this->m_path.c_str ());
            std::strncpy
                ( address.sun_path
                , path
                , sizeof (address.sun_path) - 1u
                );

            if (0 != connect
                ( fd
                , reinterpret_cast <struct sockaddr *> (& address)
                , sizeof (struct sockaddr_un)
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

    std::string const &
    UnixAddress::path (void) const
    {
        return this->m_path;
    }
}
