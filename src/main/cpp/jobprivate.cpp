// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor.h>

#include "jobprivate.h"

#include <stdexcept>

namespace
{
    static
    conveyor::JobState
    jobStateFromString (QString const & string)
    {
        if("pending" == string)
            return conveyor::PENDING;
        else if("running" == string)
            return conveyor::RUNNING;
        else if("stopped" == string)
            return conveyor::STOPPED;

        throw std::invalid_argument (string.toStdString());
    }

    static
    conveyor::JobConclusion
    jobConclusionFromString (QString const & string)
    {
        if("notconcluded" == string)
            return conveyor::NOTCONCLUDED;
        else if("ended" == string)
            return conveyor::ENDED;
        else if("failed" == string)
            return conveyor::FAILED;
        else if("cancelled" == string)
            return conveyor::CANCELLED;

        throw std::invalid_argument (string.toStdString());
    }
}

namespace conveyor
{
    JobPrivate::JobPrivate
        ( Conveyor * conveyor
        , Job * job
        , Printer * printer
        , const int & id
        )
        : m_conveyor(conveyor)
        , m_job(job)
        , m_printer(printer)
        , m_id(id)
    {

    }

    void
    JobPrivate::updateFromJson(Json::Value const & json)
    {
        int const id(json["id"].asInt());
        QString const name(json["name"].asCString());
        JobState const state
            ( jobStateFromString
              ( QString(json["state"].asCString())));
        JobConclusion const conclusion
            ( jobConclusionFromString
              ( QString(json["conclusion"].asCString())));

        QString const currentStepName(json["currentstep"]["name"].asCString());
        int const currentStepProgress(json["currentstep"]["progress"].asInt());

        m_id = id;
        m_name = name;
        m_state = state;
        m_conclusion = conclusion;
        m_currentStepName = currentStepName;
        m_currentStepProgress = currentStepProgress;
    }
}
