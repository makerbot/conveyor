// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "conveyor.h"

namespace conveyor
{
    struct ConveyorPrivate
    {
    };

    struct JobPrivate
    {
    };

    struct PrinterPrivate
    {
    };

    Conveyor::Conveyor (Address const & address __attribute__ ((unused)))
        : m_private (0)
    {
    }

    QList<JobPointer>
    Conveyor::jobs (void)
    {
        QList<JobPointer> list;
        return list;
    }

    QList<PrinterPointer>
    Conveyor::printers (void)
    {
        QList<PrinterPointer> list;
        return list;
    }

    Job::Job
        ( PrinterPointer printerPointer __attribute__ ((unused))
        , QString const & id __attribute__ ((unused))
        )
        : m_private (0)
    {
    }

    Printer::Printer
        ( ConveyorPointer conveyorPointer __attribute__ ((unused))
        , QString const & name __attribute__ ((unused))
        )
        : m_private (0)
    {
    }

    QList<JobPointer>
    Printer::jobs (void)
    {
        QList<JobPointer> list;
        return list;
    }

    JobPointer Printer::print
        ( QString const & inputFile __attribute__ ((unused))
        )
    {
        JobPointer jobPointer;
        return jobPointer;
    }

    JobPointer Printer::printToFile
        ( QString const & inputFile __attribute__ ((unused))
        , QString const & outputFile __attribute__ ((unused))
        )
    {
        JobPointer jobPointer;
        return jobPointer;
    }

    JobPointer Printer::slice
        ( QString const & inputFile __attribute__ ((unused))
        , QString const & outputFile __attribute__ ((unused))
        )
    {
        JobPointer jobPointer;
        return jobPointer;
    }
}
