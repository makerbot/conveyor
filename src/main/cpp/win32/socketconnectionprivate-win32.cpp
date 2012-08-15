// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <windows.h>

#include "../socketconnectionprivate.h"

namespace conveyor
{
    bool
    SocketConnectionPrivate::invalidSocket
        ( SocketConnectionPrivate::socket_t fd
        )
    {
        return INVALID_SOCKET == fd;
    }
}
