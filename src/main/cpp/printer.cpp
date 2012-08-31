// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>

#include <conveyor.h>
#include <conveyor/exceptions.h>

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

    QList<Job *>
    Printer::jobs ()
    {
        const QList<Job *> all_jobs(m_private->m_conveyor->jobs());
        QList<Job *> result;

        // Filter the list of jobs to just those jobs whose printer
        // matches this printer
        const int len = all_jobs.size();
        for (int i = 0; i < len; ++i) {
            Job * j = all_jobs[i];
            // TODO: any reason why this should use uniqueName rather
            // than the Printer address?
            if (j->m_private->m_printer == this)
                result.append(j);
        }

        return result;
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
    Printer::print (QString const & inputFile
                    , const SlicerConfiguration & slicer_conf)
    {
        Job * const result (this->m_private->print (inputFile,
                                                    slicer_conf));
        return result;
    }

    Job *
    Printer::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        )
    {
        Job * const result (this->m_private->printToFile (inputFile,
                                                          outputFile,
                                                          slicer_conf));
        return result;
    }

    Job *
    Printer::slice
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        )
    {
        Job * const result (this->m_private->slice (inputFile,
                                                    outputFile,
                                                    slicer_conf));
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
        QString message("Printer::jog x=%1 y=%2 z=%3 a=%4 b=%5 f=%6");
        message = message.arg(x).arg(y).arg(z).arg(a).arg(b).arg(f);
        throw NotImplementedError(message.toStdString());
    }

    void
    Printer::emitChanged (void)
    {
        emit changed();
    }
}
