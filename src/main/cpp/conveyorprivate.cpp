// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QString>

#include <string>

#ifdef _WIN32
# include <winsock2.h>
# include <ws2tcpip.h>
#endif

#include <jsoncpp/json/value.h>
#include <jsonrpc/jsonrpc.h>

#include <conveyor/connection.h>
#include <conveyor/connectionstatus.h>
#include <conveyor/conveyor.h>
#include <conveyor/eeprommap.h>
#include <conveyor/exceptions.h>
#include <conveyor/job.h>
#include <conveyor/log.h>
#include <conveyor/slicers.h>

#include "connectionstream.h"
#include "connectionthread.h"
#include "conveyorprivate.h"
#include "jobprivate.h"
#include "synchronouscallback.h"

namespace conveyor
{

    void
    ConveyorPrivate::initialize()
    {
#ifdef _WIN32
        WORD wVersionRequested;
        WSADATA wsaData;
        int err;

        /* Use the MAKEWORD(lowbyte, highbyte) macro declared in Windef.h */
        wVersionRequested = MAKEWORD(2, 2);

        err = WSAStartup(wVersionRequested, &wsaData);
        if (err != 0) {
            /* Tell the user that we could not find a usable */
            /* Winsock DLL.                                  */
            QString message("WSAStartup failed with error: %1");
            message.arg(err);
            throw InitializationError(message.toStdString());
        }
#endif
    }

    Conveyor *
    ConveyorPrivate::connect (Address const * const address)
    {
        Connection * const connection (address->createConnection ());
        ConnectionStream * const connectionStream
            ( new ConnectionStream (connection)
            );
        JsonRpc * const jsonRpc (new JsonRpc (connectionStream));
        ConnectionThread * const connectionThread
            ( new ConnectionThread (connection, jsonRpc)
            );
        connectionThread->start ();
        try
        {
            Json::Value const hello
                ( SynchronousCallback::invoke
                    ( jsonRpc
                    , "hello"
                    , Json::Value (Json::arrayValue)
                    )
                );
            Conveyor * const conveyor
                ( new Conveyor
                    ( connection
                    , connectionStream
                    , jsonRpc
                    , connectionThread
                    )
                );
            return conveyor;
        }
        catch (...)
        {
            connectionThread->stop ();
            connectionThread->wait ();

            delete connectionThread;
            delete jsonRpc;
            delete connectionStream;
            delete connection;

            throw;
        }
    }

    ConveyorPrivate::ConveyorPrivate
        ( Conveyor * const conveyor
        , Connection * const connection
        , ConnectionStream * const connectionStream
        , JsonRpc * const jsonRpc
        , ConnectionThread * const connectionThread
        )
        : m_conveyor (conveyor)
        , m_connection (connection)
        , m_connectionStream (connectionStream)
        , m_jsonRpc (jsonRpc)
        , m_connectionThread (connectionThread)
        , m_printerAddedMethod(this)
        , m_printerChangedMethod(this)
        , m_printerRemovedMethod(this)
        , m_jobAddedMethod(this)
        , m_jobChangedMethod(this)
        , m_portAttachedMethod(conveyor)
        , m_portDetachedMethod(conveyor)
    {
        this->m_jsonRpc->addMethod("printeradded", & m_printerAddedMethod);
        this->m_jsonRpc->addMethod("printerchanged", & m_printerChangedMethod);
        this->m_jsonRpc->addMethod("printerremoved", & m_printerRemovedMethod);
        this->m_jsonRpc->addMethod("jobadded", & m_jobAddedMethod);
        this->m_jsonRpc->addMethod("jobchanged", & m_jobChangedMethod);
        this->m_jsonRpc->addMethod("machine_temperature_changed",
                                     &m_printerChangedMethod);
        this->m_jsonRpc->addMethod("machine_state_changed",
                                     &m_printerChangedMethod);

        this->m_jsonRpc->addMethod("port_attached",
                                   &m_portAttachedMethod);
        this->m_jsonRpc->addMethod("port_detached",
                                   &m_portDetachedMethod);
    }

    ConveyorPrivate::~ConveyorPrivate (void)
    {
        this->m_connectionThread->stop ();
        this->m_connectionThread->wait ();

        delete this->m_connectionThread;
        delete this->m_jsonRpc;
        delete this->m_connectionStream;
        delete this->m_connection;
    }

    static bool printerCompare(const Printer *p1, const Printer *p2)
    {
        return p1->displayName() < p2->displayName();
    }

    QList<Printer *>
    ConveyorPrivate::printers()
    {
        Json::Value params (Json::arrayValue);
        Json::Value const results
            ( SynchronousCallback::invoke
                ( this->m_jsonRpc
                , "getprinters"
                , params
                )
            );

        QList<Printer*> activePrinters;
        for (unsigned i = 0; i < results.size(); i++)
        {
            const Json::Value &r(results[i]);

            Printer * const printer
                ( printerByUniqueName
                    ( QString(r["uniqueName"].asCString())));

            printer->m_private->updateFromJson(r);

            if (!printer->canPrint() ||
                (printer->state() != Printer::kInvalid &&
                 printer->state() != Printer::kDisconnected)) {
                activePrinters.append(printer);
            }
        }

        // Sort the list so that it always appears in the same order
        // in the UI. This is mainly for archetype printers; it's nice
        // to have them in order.
        qSort(activePrinters.begin(),
              activePrinters.end(),
              printerCompare);

        return activePrinters;
    }

    Printer *
    ConveyorPrivate::printerByUniqueName(QString uniqueName)
    {
        Printer * p = m_printers.value(uniqueName);

        if(p == 0) {
            p = new Printer(this->m_conveyor, uniqueName);
            m_printers.insert(uniqueName, p);
        }

        return p;
    }

    /**
       Get a list jobs from the server.
       
       TODO: is there any filtering that needs to happen here?

       The Job objects are cached, so any subsequent access of the
       same job (which is referenced by its unique numeric ID) will
       return the same Job object.

       At present, Job objects live as long as Conveyor, so its safe
       to keep references to a Job even after the Job has finished.
     */
    QList<Job *>
    ConveyorPrivate::jobs()
    {
        Json::Value params (Json::arrayValue);
        Json::Value const results
            ( SynchronousCallback::invoke
                ( this->m_jsonRpc
                , "getjobs"
                , params
                )
            );

        const Json::Value::Members &ids(results.getMemberNames());

        QList<Job *> jobs;
        for (unsigned i = 0; i < ids.size(); i++)
        {
            // Job ID is sent as a string
            const std::string &key(ids[i]);
            int id = QString(key.c_str()).toInt();

            if (results[key]["state"].asString() != "STOPPED") {
                // Look up Job by its ID. This will also create the Job
                // object if it doesn't exist already.
                Job * const job(jobById(id));

                job->updateFromJson(results[key]);
                jobs.append(job);
            }
        }

        return jobs;
    }

    Job *
    ConveyorPrivate::jobById(int id)
    {
        Job * job = m_jobs.value(id);

        if (!job) {
            job = new Job(this->m_conveyor, id);
            m_jobs.insert(id, job);
        }

        return job;
    }

    static void
    setDriverNameParam(Json::Value &params)
    {
        params["driver_name"] = "s3g";
    }

    static void
    setProfileNameParam(Json::Value &params,
                        const Printer * const printer)
    {
        params["profile_name"] = printer->profileName().toStdString();
    }

    static Json::Value
    commonPrintSliceParams
        ( const SlicerConfiguration & slicerConf
        , QString const & inputFile
        , QString const & materialName
        )
    {
        Json::Value params(Json::objectValue);
        switch (slicerConf.extruder()) {
          case SlicerConfiguration::Left:
            params["extruder_name"] = "1";
            break;
          case SlicerConfiguration::Right:
            params["extruder_name"] = "0";
            break;
          case SlicerConfiguration::LeftAndRight:
            params["extruder_name"] = "0, 1";
            break;
        }
        params["gcode_processor_names"] = Json::nullValue;
        params["input_file"] = inputFile.toStdString();
        params["material_name"] = Json::Value(materialName.toStdString());
        params["slicer_name"] = slicerConf.slicerName().toLower().toStdString();
        params["slicer_settings"] = slicerConf.toJSON();

        return params;
    }

    Job *
    ConveyorPrivate::print
        ( Printer * const printer
        , QString const & inputFile
        , const SlicerConfiguration & slicerConf
        , QString const & materialName
        , bool const hasStartEnd 
        )
    {
        Json::Value params(commonPrintSliceParams(slicerConf,
                                                  inputFile,
                                                  materialName));

        params["machine_name"] = printer->uniqueName().toStdString();
        params["has_start_end"] = hasStartEnd;

        LOG_INFO << "print params=" << params.toStyledString() << std::endl;

        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "print", params)
            );

        return jobById(result["id"].asInt());
    }

    Job *
    ConveyorPrivate::printToFile
        ( Printer * const printer
        , QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicerConf
        , QString const & materialName
        , bool const hasStartEnd 
        , QString const & printToFileType
        )
    {
        Json::Value params(commonPrintSliceParams(slicerConf,
                                                  inputFile,
                                                  materialName));

        setDriverNameParam(params);
        setProfileNameParam(params, printer);
        params["file_type"] = Json::Value (printToFileType.toStdString());
        params["output_file"] = Json::Value (outputFile.toStdString ());
        params["has_start_end"] = hasStartEnd;

        LOG_INFO << "print_to_file params="
                 << params.toStyledString() << std::endl;

        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc,
                                           "print_to_file",
                                           params)
            );

        return jobById(result["id"].asInt());
    }



    Job *
    ConveyorPrivate::slice
        ( Printer * const printer
        , QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicerConf
        , QString const & materialName
        , bool const addStartEnd
        )
    {
        Json::Value params(commonPrintSliceParams(slicerConf,
                                                  inputFile,
                                                  materialName));

        setDriverNameParam(params);
        setProfileNameParam(params, printer);
        params["output_file"] = Json::Value(outputFile.toStdString ());
        params["add_start_end"] = Json::Value(addStartEnd);

        LOG_INFO << "slice params="
                 << params.toStyledString() << std::endl;

        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "slice", params)
            );

        return jobById(result["id"].asInt());
    }

    Json::Value
    ConveyorPrivate::m_getUploadableMachines(void)
    {
        Json::Value params (Json::objectValue);
        setDriverNameParam(params);
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "getuploadablemachines", params)
            );
        return result;
    }

    Json::Value
    ConveyorPrivate::m_getMachineVersions(QString machineType)
    {
        Json::Value params (Json::objectValue);
        setDriverNameParam(params);
        params["machine_type"] = Json::Value (machineType.toStdString());
        
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "getmachineversions", params)
            );
        return result;
    }

    QString
    ConveyorPrivate::m_downloadFirmware
            ( const QString &machinetype
            , const QString &version
            )
    {
        Json::Value params (Json::objectValue);
        setDriverNameParam(params);
        params["machine_type"] = Json::Value (machinetype.toStdString());
        params["firmware_version"] = Json::Value (version.toStdString());
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "downloadfirmware", params)
            );
        return result.asCString();
    }

    void
    ConveyorPrivate::m_uploadFirmware
    	( Printer * const printer
        , QString machineType
        , QString hexPath)
    {
        Json::Value params (Json::objectValue);
        params["machine_name"] = Json::Value (printer->uniqueName().toStdString());
        params["machinetype"] = Json::Value (machineType.toStdString());
        params["filename"] = Json::Value (hexPath.toStdString());
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "uploadfirmware", params)
            );
    }

    EepromMap
    ConveyorPrivate::readEeprom(Printer * const printer) const
    {
        Json::Value params (Json::objectValue);
        params["printername"] = printer->uniqueName().toStdString();
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "readeeprom", params)
            );
        EepromMap map (result);
        return map;
    }

    void
    ConveyorPrivate::writeEeprom(Printer * const printer, EepromMap map)
    {
        Json::Value params (Json::objectValue);
        params["printername"] = printer->uniqueName().toStdString();
        params["eeprommap"] = map.getEepromMap();
        SynchronousCallback::invoke (this->m_jsonRpc, "writeeeprom", params);
    }

    void ConveyorPrivate::resetToFactory(Printer * const printer) const
    {
        Json::Value params (Json::objectValue);
        params["machine_name"] = printer->uniqueName().toStdString();
        SynchronousCallback::invoke (this->m_jsonRpc, "resettofactory", params);
    }

    bool ConveyorPrivate::compatibleFirmware(QString &firmwareVersion) const
    {
        Json::Value params (Json::objectValue);
        params["firmwareversion"] = firmwareVersion.toStdString();
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "compatiblefirmware", params)
            );
        bool compatible = result.asBool();
        return compatible;
    }

    bool ConveyorPrivate::verifyS3g(QString &s3gPath) const
    {
        Json::Value params (Json::objectValue);
        params["s3gpath"] = s3gPath.toStdString();
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "verifys3g", params)
            );
        bool valid = result.asBool();
        return valid;
    }

    std::list<Port>
    ConveyorPrivate::getPorts() const
    {
        Json::Value params (Json::objectValue);
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "getports", params)
            );
        std::list<Port> ports;
        if (result.isArray()) {
            const int end(result.size());
            for (int i = 0; i < end; i++) {
                ports.push_back(Port(result[i]));
            }
        }
        return ports;
    }

    void
    ConveyorPrivate::connectToPort(const Port &port) const
    {
      Json::Value params (Json::objectValue);
      // TODO(nicholasbishop)
      params["machine_name"] = Json::nullValue;
      params["port_name"] = port.m_name;
      params["driver_name"] = Json::nullValue;
      params["profile_name"] = Json::nullValue;
      params["persistent"] = false;
      Json::Value result
          ( SynchronousCallback::invoke (this->m_jsonRpc, "connect", params)
            );
    }

    void
    ConveyorPrivate::cancelJob (int jobId)
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        
        params["id"] = Json::Value(jobId);
        
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "canceljob", params)
              );
            
        // TODO: check result?
    }
    
    void
    ConveyorPrivate::emitPrinterAdded (Printer * const p)
    {
        m_conveyor->emitPrinterAdded(p);
    }

    void
    ConveyorPrivate::emitPrinterChanged (Printer * const p)
    {
        p->emitChanged();
    }

    void
    ConveyorPrivate::emitPrinterRemoved (Printer * const p)
    {
        m_conveyor->emitPrinterRemoved(p);
        // Disconnect all event listeners from the printer object.
        p->disconnect();
    }

    void
    ConveyorPrivate::emitJobAdded (Job * const j)
    {
        m_conveyor->emitJobAdded(j);
    }

    void
    ConveyorPrivate::emitJobChanged (Job * const j)
    {
        j->emitChanged();
    }

    void
    ConveyorPrivate::emitJobRemoved (Job * const j)
    {
        m_conveyor->emitJobRemoved(j);
    }

    bool isJobForPrinter(
        const Job * const job, const Printer * const printer)
    {
      return (
          // Physical printer
          (printer->canPrint() &&
           !job->machineName().isEmpty() &&
           job->machineName() == printer->uniqueName()) ||
          // Archetype printer
          (!printer->canPrint() &&
           !job->profileName().isEmpty() &&
           job->profileName() == printer->profileName()));
    }

    QList<Job *> filterJobsByPrinter(
        const QList<Job *> jobs, const Printer * const printer)
    {
        QList<Job *> filteredJobs;
        if (printer) {
            for (int i = 0; i < jobs.size(); i++) {
                Job * const job(jobs[i]);
                if (isJobForPrinter(job, printer)) {
                    filteredJobs.append(job);
                }
            }
        } else {
            LOG_ERROR << "Null printer parameter" << std::endl;
        }
        return filteredJobs;
    }

    QList<Job *> filterJobsByConclusion(
        const QList<Job *> jobs, const JobConclusion jobConclusion)
    {
        QList<Job *> filteredJobs;
        for (int i = 0; i < jobs.size(); i++) {
            Job * const job(jobs[i]);
            if (job->conclusion() == jobConclusion) {
                filteredJobs.append(job);
            }
        }
        return filteredJobs;
    }
}
