// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor.h>

#include "printerprivate.h"

namespace conveyor
{
    PrinterPrivate::PrinterPrivate
        ( Conveyor * const conveyor
        , Printer * const printer
        , QString const & uniqueName
        )
        : m_conveyor (conveyor)
        , m_printer (printer)
        , m_uniqueName (uniqueName)
    {
        this->m_canPrint = true;
        this->m_canPrintToFile = true;
        this->m_connectionStatus = NOT_CONNECTED;
        this->m_displayName = "Dummy Printer";
        this->m_printerType = "Replicator";
        this->m_numberOfToolheads = 2;
        this->m_hasHeatedPlatform = true;
        this->m_jobs = conveyor->jobs();
    }

    Job *
    PrinterPrivate::print (QString const & inputFile)
    {
        Job * const result
            ( this->m_conveyor->m_private->print
                ( this->m_printer
                , inputFile
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->printToFile
                ( this->m_printer
                , inputFile
                , outputFile
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::slice
        ( QString const & inputFile
        , QString const & outputFile
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->slice
                ( this->m_printer
                , inputFile
                , outputFile
                )
            );
        return result;
    }
}
