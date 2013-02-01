// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor/conveyor.h>
#include <conveyor/job.h>
#include <conveyor/log.h>

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
        , m_type(Job::kInvalidType)
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

        const std::string machineNameKey("machine_name");
        if (json.isMember(machineNameKey) &&
            json[machineNameKey].isString()) {
            m_machineName =
                QString::fromUtf8(json[machineNameKey].asCString());
        }
        const std::string profileNameKey("profile_name");
        if (json.isMember(profileNameKey) &&
            json[profileNameKey].isString()) {
            m_profileName =
                QString::fromUtf8(json[profileNameKey].asCString());
        }

        const std::string typeKey("type");
        if (json.isMember(typeKey)) {
            if (json[typeKey].isString()) {
                const std::string type(json[typeKey].asString());
                if (type == "PRINT_JOB") {
                    m_type = Job::kPrint;
                } else if (type == "PRINT_TO_FILE_JOB") {
                    m_type = Job::kPrintToFile;
                } else if (type == "SLICE_JOB") {
                    m_type = Job::kSlice;
                } else {
                    LOG_ERROR << "job type invalid value" << std::endl;
                    m_type = Job::kInvalidType;
                }
            } else {
                LOG_ERROR << "job type field not a string" << std::endl;
            }
        } else {
            LOG_ERROR << "job type field missing" << std::endl;
        }
    }
    
    void
    JobPrivate::cancel (void)
    {
        m_conveyor->cancelJob(m_id);
    }

    QString jobTypeToHumanString(const Job::Type type)
    {
        switch (type) {
            case Job::kPrint:
                return QObject::tr("Print");
            case Job::kPrintToFile:
                return QObject::tr("Print to file");
            case Job::kSlice:
                return QObject::tr("Slice");
            case Job::kInvalidType:
                break;
        }
        return QObject::tr("Unknown job type");
    }
}
