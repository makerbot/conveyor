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
    void
    Conveyor::initialize ()
    {
        ConveyorPrivate::initialize ();
    }

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

    void
    Conveyor::cancelJob (int jobId)
    {
        m_private->cancelJob(jobId);
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

    Printer*
    Conveyor::printerByUniqueName(QString name) {
        return m_private->printerByUniqueName(name);
    }

    Json::Value
    Conveyor::getUploadableMachines(void)
    {
        return m_private->m_getUploadableMachines();
    }

    Json::Value
    Conveyor::getMachineVersions(QString machinetype)
    {
        return m_private->m_getMachineVersions(machinetype);
    }

    QString
    Conveyor::downloadFirmware
            ( const QString &machinetype
            , const QString &version
            )
    {
        return m_private->m_downloadFirmware(machinetype, version);
    }
    
    void
    Conveyor::uploadFirmware(Printer * const printer, QString machinetype, QString hexPath)
    {
        m_private->m_uploadFirmware(printer, machinetype, hexPath);
    }

    EepromMap
    Conveyor::readEeprom (Printer * const printer) const
    {
        return m_private->readEeprom(printer);
    }

    void
    Conveyor::writeEeprom(Printer * const printer, EepromMap map)
    {
        m_private->writeEeprom(printer, map);
    }

    void
    Conveyor::resetToFactory(Printer * const printer) const
    {
        m_private->resetToFactory(printer);
    }

    bool
    Conveyor::compatibleFirmware(QString &firmwareVersion) const
    {
        return m_private->compatibleFirmware(firmwareVersion);
    }

    bool
    Conveyor::verifyS3g(QString &s3gPath) const
    {
        return m_private->verifyS3g(s3gPath);
    }

    std::list<Port>
    Conveyor::getPorts() const
    {
        return m_private->getPorts();
    }

    void
    Conveyor::connectToPort(const Port &port) const
    {
      m_private->connectToPort(port);
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

    void Conveyor::emitPortAttached(const Port * const port)
    {
      emit portAttached(port);
    }

    void Conveyor::emitPortDetached(const QString &portName)
    {
      emit portDetached(portName);
    }
}
