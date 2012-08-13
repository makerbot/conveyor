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
#include "printerprivate.h"

namespace conveyor
{
    class ConveyorPrivate
    {
    public:
        static ConveyorPrivate * connect (Address const * address);

        ConveyorPrivate
            ( Connection * connection
            , ConnectionStream * connectionStream
            , JsonRpc * jsonRpc
            , ConnectionThread * connectionThread
            );

        ~ConveyorPrivate (void);

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

        Connection * const m_connection;
        ConnectionStream * const m_connectionStream;
        JsonRpc * const m_jsonRpc;
        ConnectionThread * const m_connectionThread;
        QList<Job *> m_jobs;
    };
}

#endif
