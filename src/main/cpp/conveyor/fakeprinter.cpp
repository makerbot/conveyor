#include "fakeprinter.h"

#include <QDebug>
#include <QTime>

#include "conveyorprivate.h"

namespace conveyor
{

    FakePrinter::FakePrinter
		( Conveyor * convey
		, QString const & name
		) 
		: Printer(convey, name)
	{
		qsrand(QTime::currentTime().msec());
		connect(&m_connectionTimer, SIGNAL(timeout()), 
				this, SLOT(emitRandomConnectionStatus()));
	}
		
    FakePrinter::FakePrinter
		( Conveyor * convey
		, const QString &name
		, const bool &canPrint
		, const bool &canPrintToFile
		, const ConnectionStatus &cs
		, const QString &printerType
		, const int &numberOfExtruders
		, const bool &hasHeatedPlatform
		)
		: Printer
		( convey
		, name
		, canPrint
		, canPrintToFile
		, cs
		, printerType
		, numberOfExtruders
		, hasHeatedPlatform)
    {
		qsrand(QTime::currentTime().msec());
        connect(&m_connectionTimer, SIGNAL(timeout()), this, SLOT(emitRandomConnectionStatus()));
    }
	
    void FakePrinter::startRandomConnectionStatus()
    {
        m_connectionTimer.start(1000);

    }
    void FakePrinter::stopRandomConnectionStatus()
    {
        m_connectionTimer.stop();
    }
    void FakePrinter::emitRandomConnectionStatus()
    {
        int rnd = qrand();
        if(rnd % 4 == 0) //one fourth of the time actually swap stuff
        {
            qDebug() << "emitting connection status change! for printer:" << m_private->m_displayName;
			
			ConnectionStatus status = connectionStatus();
			status = (status == CONNECTED) ? NOT_CONNECTED : CONNECTED;
			
			m_private->m_connectionStatus = status;
            emit connectionStatusChanged(status);
        }
    }

    void FakePrinter::startCurrentJob()
    {
        m_jobTimer.start(1000);
    }

    void FakePrinter::stopCurrentJob()
    {
        m_jobTimer.stop();
    }

    void FakePrinter::togglePaused()
    {
        Printer::togglePaused();

        if(this->currentJob()->jobStatus() == PAUSED)
        {
            stopCurrentJob();
        }
        else if(this->currentJob()->jobStatus() == PRINTING)
        {
            startCurrentJob();
        }
    }

    Job *
    FakePrinter::print
        ( QString const & inputFile
        )
    {
        Job * job = Printer::print(inputFile);
        connect(&m_jobTimer, SIGNAL(timeout()), job, SLOT(incrementProgress()));
        return job;
    }

    Job *
    FakePrinter::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        )
    {

        Job * job = Printer::printToFile(inputFile, outputFile);
        connect(&m_jobTimer, SIGNAL(timeout()), job, SLOT(incrementProgress()));
        return job;
    }

    Job *
    FakePrinter::slice
        ( QString const & inputFile
        , QString const & outputFile
        )
    {
        Job * job = Printer::slice(inputFile, outputFile);
        connect(&m_jobTimer, SIGNAL(timeout()), job, SLOT(incrementProgress()));
        return job;
    }
    void FakePrinter::cancelCurrentJob()
    {
        stopCurrentJob();
        Printer::cancelCurrentJob();
    }
}