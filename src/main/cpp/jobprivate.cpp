// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor.h>

#include "conveyorprivate.h"
#include "jobprivate.h"

#include <stdexcept>

namespace
{
    static
    conveyor::JobState
    jobStateFromString (QString const & string)
    {
        if("PENDING" == string)
            return conveyor::PENDING;
        else if("RUNNING" == string)
            return conveyor::RUNNING;
        else if("STOPPED" == string)
            return conveyor::STOPPED;

        throw std::invalid_argument (string.toStdString());
    }

    static
    conveyor::JobConclusion
    jobConclusionFromString (QString const & string)
    {
        if("ENDED" == string)
            return conveyor::ENDED;
        else if("FAILED" == string)
            return conveyor::FAILED;
        else if("CANCELED" == string)
            return conveyor::CANCELED;

        throw std::invalid_argument (string.toStdString());
    }
}

namespace conveyor
{
    JobPrivate::JobPrivate
        ( Conveyor * conveyor
        , Job * job
        , const int & id
        )
        : m_conveyor(conveyor)
        , m_job(job)
        , m_printer(0)
        , m_id(id)
        , m_state(RUNNING)
        , m_conclusion(NOTCONCLUDED)
    {

    }

    void
    JobPrivate::updateFromJson(Json::Value const & json)
    {
        int const id(json["id"].asInt());

        // This is the filename that is being sliced/printed
        QString const name(json["name"].asCString());

        // Get printer from ID
        
        if (!json["printerid"].isNull()) {
            const QString printerUniqueName = json["printerid"].asCString();
            m_printer = m_conveyor->m_private->printerByUniqueName(printerUniqueName);
        }

        JobState const state
            ( jobStateFromString
              ( QString(json["state"].asCString())));

        JobConclusion conclusion = conveyor::NOTCONCLUDED;
        if (!json["conclusion"].isNull()) {
            conclusion = jobConclusionFromString(QString(json["conclusion"].asCString()));
        }

        if (!json["currentstep"].isNull()) {
            const QString currentStepName(json["currentstep"]["name"].asCString());
            const int currentStepProgress(json["currentstep"]["progress"].asInt());

            m_currentStepName = currentStepName;
            m_currentStepProgress = currentStepProgress;
        }
        else {
            m_currentStepName = "";
            m_currentStepProgress = 0;
        }

        if (conclusion != m_conclusion)
            m_job->emitConcluded();

        m_id = id;
        m_name = name;
        m_state = state;
        m_conclusion = conclusion;
    }
    
    void
    JobPrivate::cancel (void)
    {
        m_conveyor->cancelJob(m_id);
    }
}
