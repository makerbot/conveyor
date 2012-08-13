// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>

#include <conveyor.h>
#include <conveyor/address.h>
#include <conveyor/tcpaddress.h>
#include <conveyor/unixaddress.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
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
        , QString const & name
        , int progress
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
}
