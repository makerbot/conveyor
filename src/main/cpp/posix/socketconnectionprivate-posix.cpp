// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstring>
#include <exception>
#include <string>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>

#include "../socketconnectionprivate.h"
#include <conveyor/exceptions.h>

namespace conveyor
{
    bool
    SocketConnectionPrivate::invalidSocket
        ( SocketConnectionPrivate::socket_t fd
        )
    {
        return fd < static_cast <SocketConnectionPrivate::socket_t> (0);
    }

    SocketConnectionPrivate * 
    SocketConnectionPrivate::connectUnix (std::string const & path)
    {
        SocketConnectionPrivate::socket_t const fd
            ( socket (PF_UNIX, SOCK_STREAM, 0)
            );
        if (invalidSocket (fd))
        {
            throw SocketCreateError();
        }
        else
        {
            struct sockaddr_un address;
            memset (& address, 0, sizeof (struct sockaddr_un));
            address.sun_family = AF_UNIX;
            char const * const c_path (path.c_str ());
            std::strncpy
                ( address.sun_path
                , c_path
                , sizeof (address.sun_path) - 1u
                );

            if (0 != connect
                ( fd
                , reinterpret_cast <struct sockaddr *> (& address)
                , sizeof (struct sockaddr_un)
                ))
            {
                throw SocketConnectError(path);
            }
            else
            {
                SocketConnectionPrivate * const private_
                    ( new SocketConnectionPrivate (fd)
                    );
                return private_;
            }
        }
    }
}
