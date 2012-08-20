// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>

#include <conveyor.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    Printer::Printer
        ( Conveyor * const conveyor
        , QString const & uniqueName
        )
        : m_private
            ( new PrinterPrivate (conveyor, this, uniqueName)
            )
    {
    }

    Printer::~Printer ()
    {
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
        return m_private->m_hasHeatedPlatform;
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
        return m_private->m_conveyor;
    }

    Job *
    Printer::print (QString const & inputFile)
    {
        Job * const result (this->m_private->print (inputFile));
        return result;
    }

    Job *
    Printer::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        )
    {
        Job * const result (this->m_private->printToFile (inputFile, outputFile));
        return result;
    }

    Job *
    Printer::slice
        ( QString const & inputFile
        , QString const & outputFile
        )
    {
        Job * const result (this->m_private->slice (inputFile, outputFile));
        return result;
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
//        emit m_private->m_conveyor->jobRemoved();
    }
}
