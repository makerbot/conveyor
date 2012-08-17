// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QDebug>
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
    {
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

    /*  Commented out rather than deleted in case we need to fall back on the polling method
    QList<ConveyorPrivate::PrinterScanResult>
    ConveyorPrivate::printerScan()
    {
        Json::Value params (Json::arrayValue);
        const Json::Value results(invoke_sync(this->m_jsonRpc, "printer_scan", params));

        QList<PrinterScanResult> list;

        for (unsigned i = 0; i < results.size(); i++) {
            const Json::Value &r(results[i]);

            // XXX: not sure what key indicates a valid entry, so
            // using "iSerial" for now
            if (r["iSerial"] != Json::nullValue) {
                const PrinterScanResult li = {
                    r["pid"].asInt(),
                    r["vid"].asInt(),
                    QString(r["iSerial"].asCString()),
                    QString(r["port"].asCString())
                };
                list.push_back(li);
            }
        }

        return list;
    } */

    QList<Printer *> &
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

        m_printers.clear();

        qDebug() << QString(results.toStyledString().c_str());

        for (unsigned i = 0; i < results.size(); i++)
        {
            const Json::Value &r(results[i]);

            Printer * p
                ( new Printer
                    ( this->m_conveyor
                    , QString(r["uniqueName"].asCString())
                    , r["canPrint"].asBool()
                    , r["canPrintToFile"].asBool()
                    , connectionStatusFromString(QString(r["connectionStatus"].asCString()))
                    , QString(r["printerType"].asCString())
                    , r["numberOfToolheads"].asInt()
                    , r["hasHeatedPlatform"].asBool()
                    )
                );
            m_printers.push_back(p);
        }

        return m_printers;
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
}
