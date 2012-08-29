// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QScopedPointer>
#include <QTimer>

#include <conveyor/address.h>
#include <conveyor/conveyor.h>
#include <conveyor/eeprommap.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    Conveyor *
    Conveyor::connectToDaemon (Address const * address)
    {
        return ConveyorPrivate::connect (address);
    }

    Conveyor::Conveyor
        ( Connection * const connection
        , ConnectionStream * const connectionStream
        , JsonRpc * const jsonRpc
        , ConnectionThread * const connectionThread
        )
        : m_private
            ( new ConveyorPrivate
                ( this
                , connection
                , connectionStream
                , jsonRpc
                , connectionThread
                )
            )
    {
    }

    Conveyor::~Conveyor (void)
    {
    }

    QList<Printer *>
    Conveyor::printers (void)
    {
        return m_private->printers();
    }

    QList<Job *>
    Conveyor::jobs (void)
    {
        return m_private->jobs();
    }

    EepromMap
    Conveyor::readEeprom (void) const
    {
        return m_private->readEeprom();
    }

    void
    Conveyor::writeEeprom(EepromMap map)
    {
        m_private->writeEeprom(map);
    }

    void
    Conveyor::emitPrinterAdded (Printer * const p)
    {
        emit printerAdded(p);
    }

    void
    Conveyor::emitPrinterRemoved (Printer * const p)
    {
        emit printerRemoved(p);
    }

    void
    Conveyor::emitJobAdded (Job * const j)
    {
        emit jobAdded(j);
    }

    void
    Conveyor::emitJobRemoved (Job * const j)
    {
        emit jobRemoved(j);
    }
}
