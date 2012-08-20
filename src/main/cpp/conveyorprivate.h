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
#include "printerremovedmethod.h"
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

        QList<Printer *> printers();

        Printer * printerByUniqueName(QString uniqueName);

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

        Conveyor * const m_conveyor;
        Connection * const m_connection;
        ConnectionStream * const m_connectionStream;
        JsonRpc * const m_jsonRpc;
        ConnectionThread * const m_connectionThread;

        PrinterAddedMethod m_printerAddedMethod;
        PrinterRemovedMethod m_printerRemovedMethod;
        
        QList<Job *> m_jobs;
        QHash<QString, Printer *> m_printers;

        void emitPrinterAdded(Printer *);
        void emitPrinterRemoved(Printer *);
    };
}

#endif
