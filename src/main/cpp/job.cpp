// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>
#include <QScopedPointer>

#include <conveyor/exceptions.h>
#include <conveyor/job.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    Job::Job
        ( Conveyor * conveyor
        , int const & id
        )
        : m_private
          ( new JobPrivate (conveyor, this, id)
          )
    {
    }

    Job::~Job (void)
    {
    }

    int
    Job::id (void) const
    {
        return m_private->m_id;
    }

    QString
    Job::name (void) const
    {
        return m_private->m_name;
    }

    JobState
    Job::state (void) const
    {
        return m_private->m_state;
    }

    JobConclusion
    Job::conclusion (void) const
    {
        return m_private->m_conclusion;
    }

    int
    Job::currentStepProgress (void) const
    {
        return m_private->m_currentStepProgress;
    }

    QString
    Job::currentStepName (void) const
    {
        return m_private->m_currentStepName;
    }

    void
    Job::cancel (void)
    {
        m_private->cancel();
    }
    
    void
    Job::pause (void)
    {
        throw NotImplementedError("Job::pause");
    }
    
    void
    Job::emitChanged (void)
    {
        emit changed(this);
    }

    void
    Job::emitConcluded (void)
    {
        emit concluded(this);
    }

    QString Job::machineName() const
    {
        return m_private->m_machineName;
    }

    QString Job::profileName() const
    {
        return m_private->m_profileName;
    }
}
