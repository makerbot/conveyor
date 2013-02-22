// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "jobaddedmethod.h"
#include "jobprivate.h"
#include "conveyorprivate.h"

#include <conveyor/job.h>

#include <QString>
#include <QMetaObject>

#include <QDebug>

namespace conveyor
{
    JobAddedMethod::JobAddedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    JobAddedMethod::~JobAddedMethod (void)
    {
    }
    
    Json::Value JobAddedMethod::invoke (Json::Value const & params)
    {
        const int id(params["id"].asInt());

        Job * job(m_conveyorPrivate->jobById(id));
        job->updateFromJson(params);

        m_conveyorPrivate->emitJobAdded(job);

        return Json::Value(Json::nullValue);
    }
}
