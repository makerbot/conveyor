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
    Job::Progress::Progress()
        : m_name(QString()),
          m_progress(0) {
    }

    Job::Failure::Failure()
        : m_failed(false),
          m_exception(QString()),
          m_code(-1),
          m_slicerLog(QString())
    {
    }

    JobPrivate::JobPrivate
        ( Conveyor * conveyor
        , Job * job
        , const int & id
        )
        : m_conveyor(conveyor)
        , m_job(job)
        , m_printer(0)
        , m_id(id)
        , m_state(PENDING)
        , m_conclusion(NOTCONCLUDED)
        , m_type(Job::kInvalidType)
    {

    }

    void
    JobPrivate::updateFromJson(Json::Value const & json)
    {
        const std::string errorStr("error in job info: " +
                                   json.toStyledString());

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

        const std::string progressKey("progress");
        if (json.isMember(progressKey) && !json[progressKey].isNull()) {
            if (json[progressKey].isObject()) {
                const std::string progressNameKey("name");
                const std::string progressProgressKey("progress");
                if (json[progressKey].isMember(progressNameKey) &&
                    json[progressKey].isMember(progressProgressKey) &&
                    json[progressKey][progressNameKey].isString() &&
                    json[progressKey][progressProgressKey].isNumeric()) {
                    m_progress.m_name = QString::fromUtf8(
                        json[progressKey][progressNameKey].asCString());
                    m_progress.m_progress =
                        json[progressKey][progressProgressKey].asInt();
                } else {
                  LOG_ERROR << errorStr << std::endl;
                }
            } else {
                LOG_ERROR << errorStr << std::endl;
            }
        } else if (m_state != STOPPED) {
          // Hack: conveyor doesn't yet set a pending state naturally,
          // so for now we assume that running jobs without progress
          // are pending
          m_state = PENDING;
        }

        const std::string failureKey("failure");
        if (json.isMember(failureKey) && !json[failureKey].isNull()) {
            if (json[failureKey].isObject()) {
                const std::string failureExceptionKey("exception");
                const std::string failureCodeKey("code");
                const std::string failureSlicerLogKey("slicerlog");
                if (json[failureKey].isMember(failureExceptionKey) &&
                    json[failureKey].isMember(failureCodeKey) &&
                    json[failureKey].isMember(failureSlicerLogKey) &&
                    json[failureKey][failureCodeKey].isNumeric() &&
                    json[failureKey][failureSlicerLogKey].isString()) {
                  const QString exc(
                      json[failureKey][failureExceptionKey].isString() ?
                      QString::fromUtf8(
                          json[failureKey][failureExceptionKey].asCString()) :
                      QString());

                  m_failure.m_failed = true;
                  m_failure.m_exception = exc;
                  m_failure.m_code =
                      json[failureKey][failureCodeKey].asInt();
                  m_failure.m_slicerLog = QString::fromUtf8(
                          json[failureKey][failureSlicerLogKey].asCString());
                } else {
                    LOG_ERROR << errorStr << std::endl;
                }
            } else {
                LOG_ERROR << errorStr << std::endl;
            }
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
