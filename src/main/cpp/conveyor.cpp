// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QScopedPointer>
#include <QTimer>

#include <conveyor/address.h>
#include <conveyor/conveyor.h>

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

    Job * 
    Conveyor::read_eeprom
        ( QString const & map_directory)
        {
            return m_private->read_eeprom(map_directory)
        }

    Job *
    Conveyor::write_eeprom
        ( JsonRpc const & eeprom_values
        , QString const & map_directory
        )
        {
            return m_private->write_eeprom(eeprom_values, map_directory)
        }

    QList<Job *>
    Conveyor::jobs (void)
    {
        return m_private->jobs();
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
