// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <string>

#include <json/value.h>
#include <jsonrpc.h>

#include <conveyor/connection.h>
#include <conveyor/connectionstatus.h>

#include "connectionstream.h"
#include "connectionthread.h"
#include "conveyorprivate.h"
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
        , m_jobRemovedMethod(this)
    {
        this->m_jsonRpc->addMethod("printeradded", & m_printerAddedMethod);
        this->m_jsonRpc->addMethod("printerchanged", & m_printerChangedMethod);
        this->m_jsonRpc->addMethod("printerremoved", & m_printerRemovedMethod);
        this->m_jsonRpc->addMethod("jobadded", & m_jobAddedMethod);
        this->m_jsonRpc->addMethod("jobchanged", & m_jobChangedMethod);
        this->m_jsonRpc->addMethod("jobremoved", & m_jobRemovedMethod);
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

        for (unsigned i = 0; i < results.size(); i++)
        {
            const Json::Value &r(results[i]);

            Printer * const printer
                ( printerByUniqueName
                    ( QString(r["uniqueName"].asCString())));

            printer->m_private->updateFromJson(r);
        }

        return m_printers.values();
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

    QList<Job *>
    ConveyorPrivate::jobs()
    {
        //TODO: Should this look more like printers()?
        return m_jobs.values();
    }

    Job *
    ConveyorPrivate::jobById(int id)
    {
        return m_jobs.value(id);
    }

    Job *
    ConveyorPrivate::print
        ( Printer * const printer
        , QString const & inputFile
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["printername"] = null;
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["preprocessor"] = null;
        params["skip_start_end"] = Json::Value (false);
        params["archive_lvl"] = Json::Value ("all");
        params["archive_dir"] = null;
        params["slicer_settings"] = null;
        params["material"] = null;
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "print", params)
            );

        int const jobId(result["id"].asInt());

        Job * const job
            ( new Job
                ( m_conveyor
                , printer
                , jobId));

        m_jobs.insert(jobId, job);

        return job;
    }

    Job *
    ConveyorPrivate::printToFile
        ( Printer * const printer
        , QString const & inputFile
        , QString const & outputFile
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["profilename"] = null;
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["outputpath"] = Json::Value (outputFile.toStdString ());
        params["preprocessor"] = null;
        params["skip_start_end"] = Json::Value (false);
        params["archive_lvl"] = Json::Value ("all");
        params["archive_dir"] = null;
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "printToFile", params)
            );

        int const jobId(result["id"].asInt());

        Job * const job
            ( new Job
                ( m_conveyor
                , printer
                , jobId));

        m_jobs.insert(jobId, job);

        return job;
    }

    Job *
    ConveyorPrivate::slice
        ( Printer * const printer
        , QString const & inputFile
        , QString const & outputFile
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["profilename"] = null;
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["outputpath"] = Json::Value (outputFile.toStdString ());
        params["preprocessor"] = null;
        params["with_start_end"] = Json::Value (false);
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "slice", params)
            );

        int const jobId(result["id"].asInt());

        Job * const job
            ( new Job
                ( m_conveyor
                , printer
                , jobId));

        m_jobs.insert(jobId, job);

        return job;
    }

    Job *
    ConveyorPrivate::read_eeprom
        ( QString const & map_directory
        )
    {
        Json::Value params (Json::objectValue);
        params["map_directoty"] = Json::Value(map_directory.toStdString ());
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "read_eeprom", params)
            );

        return result
    }

    Job *
    ConveyorPrivate::write_eeprom
        ( JsonRpc const & eeprom_values
        , QString const & map_directory
        )
    {
        Json::Value params (Json::objectValue);
        Json::Value null;
        params["eeprom_values"] = Json::Value eeprom_values;
        params["map_directoty"] = Json::Value(map_directory.toStdString ());
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "write_eeprom", params)
            );

        return result
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
