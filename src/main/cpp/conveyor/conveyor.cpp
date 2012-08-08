// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "conveyor.h"

#include <QUuid>
#include <QDebug>

#include "conveyorprivate.h"

namespace conveyor
{

    Conveyor::Conveyor (Address const & address __attribute__ ((unused)))
        : m_private (0)
    {
    }

    QList<Job *> const &
    Conveyor::jobs ()
    {
        return m_private->m_jobs;
    }

    QList<Printer *>
    Conveyor::printers ()
    {
        QList<Printer *> list;
        return list;
    }

    Job::Job
        ( Printer * printer __attribute__ ((unused))
        , QString const & id
        )
        : m_private(new JobPrivate())
    {
        m_private->m_progress = 0;
        m_private->m_uniqueName = id;
        m_private->m_Status = PRINTING;
    }
    Job::Job
		( Printer * printer __attribute__ ((unused))
		, QString const &name
		, int const &progress
		)
		: m_private(new JobPrivate())
    {
        m_private->m_displayName = name;
        m_private->m_progress = progress;
        m_private->m_uniqueName = QUuid::createUuid().toString();
        m_private->m_Status = PRINTING;
    }
	
    int
	Job::progress()
    {
        return m_private->m_progress;
    }
	/*
    void
	Job::incrementProgress()
    {
        m_private->m_progress++;
        emit JobPercentageChanged(m_private->m_progress);
    }
	*/
    JobStatus 
	Job::jobStatus() const
    {
        return m_private->m_Status;
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
        m_private->m_Conveyor = conveyor;
    }
	
    Printer::Printer
		( Conveyor *convey
		, const QString &name
		, const bool &canPrint
		, const bool &canPrintToFile
		, const ConnectionStatus &cs
        , const QString &printerType
		, const int &numberOfExtruders
		, const bool &hasHeatedPlatform
		)
		: m_private(new PrinterPrivate())
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
        m_private->m_Conveyor = convey;
    }

    Printer::~Printer ()
    {
        delete m_private;
    }

    QList<Job *> const & 
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
	
    Conveyor * 
	Printer::conveyor()
    {
        return m_private->m_Conveyor;
    }

    Job *
    Printer::print
        ( QString const & inputFile __attribute__ ((unused))
        )
    {
        QString jobID("fakePrintID:" + QUuid::createUuid().toString());
        Job * job = new Job(this, jobID);
        m_private->m_jobs.append(job);
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
        m_private->m_jobs.append(job);
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
        m_private->m_jobs.append(job);
        return job;
    }

    void
    Printer::jog
		( float x
		, float y
		, float z
		, float a
        , float b
		, float f
		)
    {
        qDebug() << "jogging x"<<x<<" y"<<y<<" z"<<z<<" a"<<a<<" b"<<b<<" f"<<f;
        //Jogz
    }
	
    void Printer::togglePaused()
    {
        qDebug() << "1. jobstatus" << this->currentJob()->jobStatus();
        if(this->currentJob()->jobStatus() == PRINTING)
        {
            this->currentJob()->m_private->m_Status = PAUSED;
        }
        else if(this->currentJob()->jobStatus() == PAUSED)
        {
            this->currentJob()->m_private->m_Status = PRINTING;
        }
        qDebug() << "2. jobstatus" << this->currentJob()->jobStatus();

    }
	
    void Printer::cancelCurrentJob()
    {
        this->m_private->m_jobs.first()->m_private->m_Status = CANCELLED;
        emit m_private->m_Conveyor->jobRemoved();
    }

    Address WindowsDefaultAddress;
    Address UNIXDefaultAddress;

    Address&
    defaultAddress()
    {
        #if defined(CONVEYOR_ADDRESS)
            return CONVEYOR_ADDRESS;
        #elif defined(Q_OS_WIN32)
            return WindowsDefaultAddress;
        #elif defined(Q_OS_MAC)
            return UNIXDefaultAddress;
        #elif defined(Q_OS_LINUX)
            return UNIXDefaultAddress;
        #else
            #error No CONVEYOR_ADDRESS defined and no default location known for this platform
        #endif
    }
}
