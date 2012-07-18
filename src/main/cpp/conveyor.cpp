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
        QList<Job *> m_jobs;
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

    QList<Job *>
    Conveyor::jobs ()
    {
        QList<Job *> list;
        return list;
    }

    QList<Printer *>
    Conveyor::printers ()
    {
        QList<Printer *> list;
        return list;
    }

    Job::Job
        ( Printer * printer __attribute__ ((unused))
        , QString const & id __attribute__ ((unused))
        )
        : m_private (0)
    {
    }


    Printer::Printer
        ( Conveyor  * conveyor __attribute__ ((unused))
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
        m_private->m_jobs = conveyor->jobs();
    }
    Printer::Printer (Conveyor *convey, const QString &name, const bool &canPrint, const bool &canPrintToFile, const ConnectionStatus &cs,
                      const QString &printerType, const int &numberOfExtruders, const bool &hasHeatedPlatform): m_private(new PrinterPrivate())
    {
        m_private->m_canPrint = canPrint;
        m_private->m_canPrintToFile = canPrintToFile;
        m_private->m_connectionStatus = cs;
        m_private->m_displayName = name;
        m_private->m_printerType = printerType;
        m_private->m_uniqueName = QUuid::createUuid().toString();
        m_private->m_numberOfToolheads = numberOfExtruders;
        m_private->m_hasPlatform = hasHeatedPlatform;
        m_private->m_jobs = convey->jobs();
    }

    Printer::~Printer ()
    {
        delete m_private;
    }

    QList<Job *>
    Printer::jobs ()
    {
       return m_private->m_jobs;
    }

    Job *
    Printer::currentJob ()
    {
        if(m_private->m_jobs.isEmpty())
            return 0;

        return m_private->m_jobs.first();
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

    bool Printer::hasHeatedPlatform() const
    {
        return m_private->m_hasPlatform;
    }

    bool
    Printer::canPrintToFile () const
    {
        return m_private->m_canPrintToFile;
    }

    int Printer::numberOfExtruders() const
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

    Job *
    Printer::print
        ( QString const & inputFile __attribute__ ((unused))
        )
    {
        QString jobID("fakePrintID:" + QUuid::createUuid().toString());
        Job * job = new Job(this, jobID);
        return job;
    }

    Job *
    Printer::printToFile
        ( QString const & inputFile __attribute__ ((unused))
        , QString const & outputFile __attribute__ ((unused))
        )
    {
        QString jobID("fakePrintToFileID:" + QUuid::createUuid().toString());
        Job * job = new Job(this, jobID);
        return job;
    }

    Job *
    Printer::slice
        ( QString const & inputFile __attribute__ ((unused))
        , QString const & outputFile __attribute__ ((unused))
        )
    {
        QString jobID("fakeSliceID:" + QUuid::createUuid().toString());
        Job * job = new Job(this, jobID);
        return job;
    }

    void
    Printer::jog(float x, float y, float z, float a, float b, float f)
    {
        qDebug() << "jogging x"<<x<<" y"<<y<<" z"<<z<<" a"<<a<<" b"<<b<<" f"<<f;
        //Jogz
    }
}
