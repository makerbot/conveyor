// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYORPRIVATE_H
#define CONVEYORPRIVATE_H

#include <QList>
#include <QString>

#include <jsonrpc.h>
#include <conveyor.h>
#include <conveyor/address.h>
#include <conveyor/connection.h>

#include "connectionstream.h"
#include "connectionthread.h"
#include "printeraddedmethod.h"
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

        /*  Commented out rather than deleted in case we need to fall back on the polling method
        struct PrinterScanResult {
            int pid;
            int vid;
            QString iSerial;
            QString port;
        };

        QList<PrinterScanResult> printerScan();
        */

        QList<Printer *> & printers();

        Job * print
            ( Printer * printer
            , QString const & inputFile
            );
        Job * printToFile
            ( Printer * printer
            , QString const & inputFile
            , QString const & outputFile
            );
        Job * slice
            ( Printer * printer
            , QString const & inputFile
            , QString const & outputFile
            );

        Conveyor * const m_conveyor;
        Connection * const m_connection;
        ConnectionStream * const m_connectionStream;
        JsonRpc * const m_jsonRpc;
        ConnectionThread * const m_connectionThread;
        
        PrinterAddedMethod m_printerAddedMethod;
        
        QList<Job *> m_jobs;
        QList<Printer *> m_printers;
    };
}

#endif
