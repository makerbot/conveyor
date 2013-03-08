// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYORPRIVATE_H
#define CONVEYORPRIVATE_H

#include <QHash>
#include <QList>
#include <QString>

#include <jsonrpc/jsonrpc.h>

#include <conveyor/address.h>
#include <conveyor/connection.h>
#include <conveyor/eeprommap.h>

#include "connectionstream.h"
#include "connectionthread.h"
#include "notification_methods.h"
#include "printeraddedmethod.h"
#include "printerchangedmethod.h"
#include "printerremovedmethod.h"
#include "jobaddedmethod.h"
#include "jobchangedmethod.h"
#include "printerprivate.h"

namespace conveyor
{
    class ConveyorPrivate
    {
    public:
        static void initialize();

        static Conveyor * connect (Address const * address);

        ConveyorPrivate
            ( Conveyor * conveyor
            , Connection * connection
            , ConnectionStream * connectionStream
            , JsonRpc * jsonRpc
            , ConnectionThread * connectionThread
            );

        ~ConveyorPrivate (void);

        /** Return a QList of pointers to all currently
            connected (and some archetype) printers. */
        QList<Printer *> printers();
        QList<Job *> jobs();

        Printer * printerByUniqueName(QString uniqueName);
        Job * jobById(int id);

        Job * print
            ( Printer * printer
            , QString const & inputFile
            , const SlicerConfiguration & slicer_conf
            , QString const & material
            , bool const hasStartEnd
            );
        Job * printToFile
            ( Printer * printer
            , QString const & inputFile
            , QString const & outputFile
            , const SlicerConfiguration & slicer_conf
            , QString const & material
            , bool const hasStartEnd
            , QString const & printToFileType
            );
        Job * slice
            ( Printer * printer
            , QString const & inputFile
            , QString const & outputFile
            , const SlicerConfiguration & slicer_conf
            , QString const & material
            , bool const addStartEnd
            );

        void cancelJob (int jobId);

        Json::Value m_getUploadableMachines(void);
        Json::Value m_getMachineVersions(QString machineType);
        QString m_downloadFirmware(const QString &machinetype, const QString &version);
        void m_uploadFirmware(Printer * const printer, QString machineType, QString hexPath);

        EepromMap readEeprom(Printer * const printer) const;
        void writeEeprom(Printer * const printer, EepromMap map);
        void resetToFactory(Printer * const printer) const;
        bool compatibleFirmware(QString &firmwareVersion) const;
        bool verifyS3g(QString &s3gPath) const;

        std::list<Port> getPorts() const;

        void connectToPort(const Port &port) const;

        Conveyor * const m_conveyor;
        Connection * const m_connection;
        ConnectionStream * const m_connectionStream;
        JsonRpc * const m_jsonRpc;
        ConnectionThread * const m_connectionThread;

        PrinterAddedMethod m_printerAddedMethod;
        PrinterChangedMethod m_printerChangedMethod;
        PrinterRemovedMethod m_printerRemovedMethod;
        JobAddedMethod m_jobAddedMethod;
        JobChangedMethod m_jobChangedMethod;
        PortAttachedMethod m_portAttachedMethod;
        PortDetachedMethod m_portDetachedMethod;

        /** Cached jobs, potentially including defunct jobs */
        QHash<int, Job *> m_jobs;

        /** Hash of all printers, connected and not. */
        QHash<QString, Printer *> m_printers;

        void emitPrinterAdded(Printer *);
        void emitPrinterChanged(Printer *);
        void emitPrinterRemoved(Printer *);

        void emitJobAdded (Job *);
        void emitJobChanged (Job *);
        void emitJobRemoved (Job *);
    };
}

#endif
