// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "conveyor.h"

#include <QUuid>

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
        QString m_displayName;
        QString m_uniqueName;

        bool m_canPrint;
        bool m_canPrintToFile;

        ConnectionStatus m_connectionStatus;
    };

    Conveyor::Conveyor (Address const & address __attribute__ ((unused)))
        : m_private (0)
    {
    }

    QList<JobPointer>
    Conveyor::jobs ()
    {
        QList<JobPointer> list;
        return list;
    }

    QList<PrinterPointer>
    Conveyor::printers ()
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
        : m_private (new PrinterPrivate())
    {
        m_private->m_canPrint = true;
        m_private->m_canPrintToFile = true;
        m_private->m_connectionStatus = NOT_CONNECTED;
        m_private->m_displayName = "Dummy Printer";
        m_private->m_uniqueName = QUuid::createUuid().toString();
    }

    Printer::~Printer ()
    {
        delete m_private;
    }

    QList<JobPointer>
    Printer::jobs ()
    {
        QList<JobPointer> list;
        return list;
    }

    QString const &
    Printer::displayName () const
    {
        return m_private->m_displayName;
    }

    QString const &
    Printer::uniqueName () const
    {
        return m_private->m_uniqueName;
    }

    bool
    Printer::canPrint () const
    {
        return m_private->m_canPrint;
    }

    bool
    Printer::canPrintToFile () const
    {
        return m_private->m_canPrintToFile;
    }

    ConnectionStatus
    Printer::connectionStatus () const
    {
        return m_private->m_connectionStatus;
    }

    QString
    Printer::connectionStatusString () const
    {
        QString status;

        switch(m_private->m_connectionStatus)
        {
        case CONNECTED:
            status = "Connected";
            break;
        case NOT_CONNECTED:
            status = "Not Connected";
            break;
        }

        return status;
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
