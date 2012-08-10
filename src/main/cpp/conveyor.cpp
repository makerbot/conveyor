// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>

#include <conveyor.h>
#include <conveyor/address.h>
#include <conveyor/tcpaddress.h>
#include <conveyor/unixaddress.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    Conveyor *
    Conveyor::connect (Address const & address)
    {
        ConveyorPrivate * const private_ (ConveyorPrivate::connect (address));
        Conveyor * const conveyor (new Conveyor (private_));
        return conveyor;
    }

    Conveyor::Conveyor (ConveyorPrivate * const private_)
        : m_private (private_)
    {
    }

    Conveyor::~Conveyor (void)
    {
        delete this->m_private;
    }

    QList<Job *> const &
    Conveyor::jobs ()
    {
        return m_private->m_jobs;
    }

    QList<Printer *>
    Conveyor::printers ()
    {
        QList<Printer *> list;
        return list;
    }

    // TODO: move the address stuff.

    TcpAddress WindowsDefaultAddress ("localhost", 9999);
    UnixAddress UNIXDefaultAddress ("conveyord.socket");

    Address&
    defaultAddress()
    {
        #if defined(CONVEYOR_ADDRESS)
            return CONVEYOR_ADDRESS;
        #elif defined(Q_OS_WIN32)
            return WindowsDefaultAddress;
        #elif defined(Q_OS_MAC)
            return UNIXDefaultAddress;
        #elif defined(Q_OS_LINUX)
            return UNIXDefaultAddress;
        #else
            #error No CONVEYOR_ADDRESS defined and no default location known for this platform
        #endif
    }
}
