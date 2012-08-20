// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <string>
#include <stdexcept>

#include <json/value.h>
#include <jsonrpc.h>

#include <conveyor/connection.h>
#include <conveyor/connectionstatus.h>

#include "connectionstream.h"
#include "connectionthread.h"
#include "conveyorprivate.h"
#include "synchronouscallback.h"

namespace
{
    static
    conveyor::ConnectionStatus
    connectionStatusFromString (QString const & string)
    {
        if("connected" == string)
            return conveyor::CONNECTED;
        else if("not connected" == string)
            return conveyor::NOT_CONNECTED;

        throw std::invalid_argument (string.toStdString());
    }
}

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
    {
        this->m_jsonRpc->addMethod("printeradded", & m_printerAddedMethod);
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

            QString const uniqueName(r["uniqueName"].asCString());
            bool const canPrint(r["canPrint"].asBool());
            bool const canPrintToFile(r["canPrintToFile"].asBool());
            ConnectionStatus const connectionStatus
                ( connectionStatusFromString
                    ( QString(r["connectionStatus"].asCString())));
            QString const printerType(QString(r["printerType"].asCString()));
            int const numberOfToolheads(r["numberOfToolheads"].asInt());
            bool const hasHeatedPlatform(r["hasHeatedPlatform"].asBool());

            Printer * const printer(printerByUniqueName(uniqueName));

            printer->m_private->m_uniqueName = uniqueName;
            printer->m_private->m_canPrint = canPrint;
            printer->m_private->m_canPrintToFile = canPrintToFile;
            printer->m_private->m_connectionStatus = connectionStatus;
            printer->m_private->m_printerType = printerType;
            printer->m_private->m_numberOfToolheads = numberOfToolheads;
            printer->m_private->m_hasHeatedPlatform = hasHeatedPlatform;

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
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "print", params)
            );
        Job * const job (new Job (printer, "0")); // TODO: fetch id from result
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
        params["printername"] = null;
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["outputpath"] = Json::Value (outputFile.toStdString ());
        params["preprocessor"] = null;
        params["skip_start_end"] = Json::Value (false);
        params["archive_lvl"] = Json::Value ("all");
        params["archive_dir"] = null;
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "printToFile", params)
            );
        Job * const job (new Job (printer, "0")); // TODO: fetch id from result
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
        params["printername"] = null;
        params["inputpath"] = Json::Value (inputFile.toStdString ());
        params["outputpath"] = Json::Value (outputFile.toStdString ());
        params["preprocessor"] = null;
        params["with_start_end"] = Json::Value (false);
        Json::Value const result
            ( SynchronousCallback::invoke (this->m_jsonRpc, "slice", params)
            );
        Job * const job (new Job (printer, "0")); // TODO: fetch id from result
        return job;
    }

    void
    ConveyorPrivate::emitPrinterAdded (Printer * const p)
    {
        m_conveyor->emitPrinterAdded(p);
    }

    void
    ConveyorPrivate::emitPrinterRemoved (Printer * const p)
    {
        m_conveyor->emitPrinterRemoved(p);
    }
}
