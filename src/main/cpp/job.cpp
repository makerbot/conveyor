// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>
#include <QMutexLocker>
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
        : m_jobPrivate
          ( new JobPrivate (conveyor, this, id)
          )
    {
    }

    Job::~Job (void)
    {
    }

    void
    Job::updateFromJson(Json::Value const &value)
    {
        const JobConclusion oldConclusion(conclusion());

        {
            QMutexLocker locker(&m_jobPrivateMutex);
            m_jobPrivate->updateFromJson(value);
        }

        if (oldConclusion != conclusion()) {
            emitConcluded();
        }
    }

    int
    Job::id (void) const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_id;
    }

    QString
    Job::name (void) const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_name;
    }

    JobState
    Job::state (void) const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_state;
    }

    JobConclusion
    Job::conclusion (void) const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_conclusion;
    }

    void
    Job::cancel (void)
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        m_jobPrivate->cancel();
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
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_machineName;
    }

    QString Job::profileName() const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_profileName;
    }

    Job::Progress Job::progress() const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_progress;
    }

    Job::Failure Job::failure() const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_failure;
    }

    Job::Type Job::type() const
    {
        QMutexLocker locker(&m_jobPrivateMutex);
        return m_jobPrivate->m_type;
    }
}
