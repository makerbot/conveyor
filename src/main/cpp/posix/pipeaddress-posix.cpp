// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor/connection.h>
#include <conveyor/pipeaddress.h>

#include "../socketconnectionprivate.h"

namespace conveyor
{
    Connection *
    PipeAddress::createConnection (void) const
    {
        SocketConnectionPrivate * const private_
            ( SocketConnectionPrivate::connectUnix (this->m_path)
            );
        Connection * const connection (new Connection (private_));
        return connection;
    }
}
