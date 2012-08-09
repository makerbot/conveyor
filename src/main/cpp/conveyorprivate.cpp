// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <json/value.h>
#include <jsonrpc.h>
#include <conveyor.h>

#include "conveyorprivate.h"

namespace
{
    static
    Json::Value
    invoke_sync
        ( JsonRpc & jsonRpc __attribute__ ((unused))
        , std::string const & methodName __attribute__ ((unused))
        , Json::Value const & params __attribute__ ((unused))
        )
    {
        // TODO: thread madness; it's okay now since conveyor-py returns null.
        jsonRpc.invoke (methodName, params, 0);
        Json::Value const null;
        return null;
    }
}

namespace conveyor
{
    ConveyorPrivate::ConveyorPrivate (JsonRpc & jsonRpc)
        : m_jsonRpc (jsonRpc)
    {
    }

    Job *
    ConveyorPrivate::print
        ( Printer * const printer
        , QString const & inputFile
        )
    {
        Json::Value params (Json::arrayValue);
        params.append(Json::Value (inputFile.toStdString ()));
        params.append(Json::Value ());
        params.append(Json::Value (false));
        Json::Value const result
            ( invoke_sync (this->m_jsonRpc, "print", params)
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
        Json::Value params (Json::arrayValue);
        params.append(Json::Value (inputFile.toStdString ()));
        params.append(Json::Value (outputFile.toStdString ()));
        params.append(Json::Value ());
        params.append(Json::Value (false));
        Json::Value const result
            ( invoke_sync (this->m_jsonRpc, "printToFile", params)
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
        Json::Value params (Json::arrayValue);
        params.append(Json::Value (inputFile.toStdString ()));
        params.append(Json::Value (outputFile.toStdString ()));
        params.append(Json::Value ());
        params.append(Json::Value (false));
        Json::Value const result
            ( invoke_sync (this->m_jsonRpc, "slice", params)
            );
        Job * const job (new Job (printer, "0")); // TODO: fetch id from result
        return job;
    }
}
