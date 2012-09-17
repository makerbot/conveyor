// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QDebug>

#include <string>

#include <json/value.h>
#include <jsonrpc.h>

#include <conveyor/connection.h>
#include <conveyor/connectionstatus.h>
#include <conveyor/eeprommap.h>


#include "connectionstream.h"
#include "connectionthread.h"
#include "conveyorprivate.h"
#include "jobprivate.h"
#include "synchronouscallback.h"

namespace conveyor
{
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
    {
        this->m_jsonRpc->addMethod("printeradded", & m_printerAddedMethod);
        this->m_jsonRpc->addMethod("printerchanged", & m_printerChangedMethod);
        this->m_jsonRpc->addMethod("printerremoved", & m_printerRemovedMethod);
        this->m_jsonRpc->addMethod("jobadded", & m_jobAddedMethod);
        this->m_jsonRpc->addMethod("jobchanged", & m_jobChangedMethod);
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
            activePrinters.append(printer);
        }

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

                job->m_private->updateFromJson(results[key]);
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

    Job *
    ConveyorPrivate::print
        ( Printer * const printer
        , QString const & inputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const skipStartEnd 
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["printername"] = printer->uniqueName().toStdString();
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["preprocessor"] = Json::Value (Json::arrayValue);
        params["skip_start_end"] = skipStartEnd;
        params["archive_lvl"] = Json::Value ("all");
        params["archive_dir"] = null;
        params["slicer_settings"] = slicer_conf.toJSON();
        params["material"] = Json::Value (material.toStdString());

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
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const skipStartEnd 
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["profilename"] = printer->uniqueName().toStdString();
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["outputpath"] = Json::Value (outputFile.toStdString ());
        params["preprocessor"] = Json::Value (Json::arrayValue);
        params["skip_start_end"] = skipStartEnd;
        params["archive_lvl"] = Json::Value ("all");
        params["archive_dir"] = null;
        params["slicer_settings"] = slicer_conf.toJSON();
        params["material"] = Json::Value (material.toStdString());

        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "printtofile", params)
            );

        return jobById(result["id"].asInt());
    }

    Json::Value
    ConveyorPrivate::m_getUploadableMachines(void)
    {
        Json::Value params (Json::objectValue);
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "getuploadablemachines", params)
            );
        return result;
    }

    Json::Value
    ConveyorPrivate::m_getMachineVersions(QString machineType)
    {
        Json::Value params (Json::objectValue);
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
        params["machinetype"] = Json::Value (machinetype.toStdString());
        params["version"] = Json::Value (version.toStdString());
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
        params["printername"] = Json::Value (printer->uniqueName().toStdString());
        params["machinetype"] = Json::Value (machineType.toStdString());
        params["filename"] = Json::Value (hexPath.toStdString());
        Json::Value result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "uploadfirmware", params)
            );
    }

    Job *
    ConveyorPrivate::slice
        ( Printer * const printer
        , QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["profilename"] = printer->uniqueName().toStdString();
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["outputpath"] = Json::Value (outputFile.toStdString ());
        params["preprocessor"] = Json::Value (Json::arrayValue);
        params["with_start_end"] = Json::Value (false);
        params["slicer_settings"] = slicer_conf.toJSON();
        params["material"] = Json::Value (material.toStdString());

        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "slice", params)
            );

        return jobById(result["id"].asInt());
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
        params["printername"] = printer->uniqueName().toStdString();
        SynchronousCallback::invoke (this->m_jsonRpc, "resettofactory", params);
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
}
