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
        QString m_printerType;
        QList<JobPointer> m_jobs;
        bool m_canPrint;
        bool m_canPrintToFile;
        bool m_hasPlatform;

        int m_numberOfToolheads;

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
        m_private->m_printerType = "Replicator";
        m_private->m_uniqueName = QUuid::createUuid().toString();
        m_private->m_numberOfToolheads = 2;
        m_private->m_hasPlatform = true;
        m_private->m_jobs = conveyorPointer->jobs();
    }

    Printer::~Printer ()
    {
        delete m_private;
    }

    QList<JobPointer>
    Printer::jobs ()
    {
       return m_private->m_jobs;
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
    QString const &
    Printer::printerType () const
    {
        return m_private->m_printerType;
    }
    bool
    Printer::canPrint () const
    {
        return m_private->m_canPrint;
    }
    bool Printer::hasPlatform() const
    {
        return m_private->m_hasPlatform;
    }
    bool
    Printer::canPrintToFile () const
    {
        return m_private->m_canPrintToFile;
    }

    int Printer::getNumberOfExtruders() const
    {
        return m_private->m_numberOfToolheads;
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
    void Printer::jog(float x, float y, float z, float f)
    {
        qDebug() << "jogging x" << x << " y" << y << " z" << z << " f" << f;
        //Jogz
    }
}
