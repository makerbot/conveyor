// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYORPRIVATE_H
#define CONVEYORPRIVATE_H

#include <QList>
#include <QString>

#include <jsonrpc.h>
#include <conveyor.h>

#include "printerprivate.h"

namespace conveyor
{
    class ConveyorPrivate
    {
    public:
        explicit ConveyorPrivate (JsonRpc & jsonRpc);

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

        JsonRpc & m_jsonRpc;
        QList<Job *> m_jobs;
    };
}

#endif
