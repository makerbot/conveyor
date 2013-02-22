// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "jobchangedmethod.h"
#include "conveyorprivate.h"
#include "jobprivate.h"

#include <conveyor/job.h>

#include <QString>
#include <QMetaObject>

#include <QDebug>

namespace conveyor
{
    JobChangedMethod::JobChangedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    JobChangedMethod::~JobChangedMethod (void)
    {
    }
    
    Json::Value JobChangedMethod::invoke (Json::Value const & params)
    {
        int const jobId(params["id"].asInt());

        Job * job(m_conveyorPrivate->jobById(jobId));

        JobState const initialJobState(job->state());

        job->updateFromJson(params);

        // Signal job-changed, and check if the job state has changed
        // to STOPPED, in which case send the job-removed signal too
        m_conveyorPrivate->emitJobChanged(job);
        if ((initialJobState != STOPPED) && job->state() == STOPPED)
            m_conveyorPrivate->emitJobRemoved(job);

        return Json::Value(Json::nullValue);
    }
}
