// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYORPRIVATE_H
#define CONVEYORPRIVATE_H

#include <QHash>
#include <QList>
#include <QString>

#include <jsonrpc.h>
#include <conveyor.h>
#include <conveyor/address.h>
#include <conveyor/connection.h>

#include "connectionstream.h"
#include "connectionthread.h"
#include "printeraddedmethod.h"
#include "printerchangedmethod.h"
#include "printerremovedmethod.h"
#include "jobaddedmethod.h"
#include "jobchangedmethod.h"
#include "jobremovedmethod.h"
#include "printerprivate.h"

namespace conveyor
{
    class ConveyorPrivate
    {
    public:
        static Conveyor * connect (Address const * address);

        ConveyorPrivate
            ( Conveyor * conveyor
            , Connection * connection
            , ConnectionStream * connectionStream
            , JsonRpc * jsonRpc
            , ConnectionThread * connectionThread
            );

        ~ConveyorPrivate (void);

        /** Return a QList of pointers to all currently connected printers. */
        QList<Printer *> printers();
        QList<Job *> jobs();

        Printer * printerByUniqueName(QString uniqueName);
        Job * jobById(int id);

        Job * print
            ( Printer * printer
            , QString const & inputFile
            , const SlicerConfiguration & slicer_conf
            );
        Job * printToFile
            ( Printer * printer
            , QString const & inputFile
            , QString const & outputFile
            , const SlicerConfiguration & slicer_conf
            );
        Job * slice
            ( Printer * printer
            , QString const & inputFile
            , QString const & outputFile
            , const SlicerConfiguration & slicer_conf
            );
            
        void cancelJob (int jobId);

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
        JobRemovedMethod m_jobRemovedMethod;

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
