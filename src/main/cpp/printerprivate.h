// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef PRINTERPRIVATE_H
#define PRINTERPRIVATE_H

#include <conveyor.h>

#include "conveyorprivate.h"

namespace conveyor
{
    class PrinterPrivate
    {
    public:
        PrinterPrivate
            ( Conveyor * conveyor
            , Printer * printer
            , QString const & uniqueName
            );

        Job * print (QString const & inputFile);
        Job * printToFile
            ( QString const & inputFile
            , QString const & outputFile
            );
        Job * slice
            ( QString const & inputFile
            , QString const & outputFile
            );

        Conveyor * const m_conveyor;
        Printer * const m_printer;
        QString m_displayName;
        QString m_uniqueName;
        QString m_printerType;
        QList<Job *> m_jobs;
        bool m_canPrint;
        bool m_canPrintToFile;
        bool m_hasHeatedPlatform;
        Conveyor * m_Conveyor;
        int m_numberOfToolheads;
        ConnectionStatus m_connectionStatus;
    };
}

#endif
