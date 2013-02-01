// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QMutex>
#include <QMutexLocker>
#include <QWaitCondition>
#include <cstdio>
#include <stdexcept>
#include <string>

#include <jsoncpp/json/value.h>
#include <jsonrpc/jsonrpc.h>
#include <jsonrpc/jsonrpcexception.h>

#include "synchronouscallback.h"

namespace
{
    static
    bool
    isErrorResponse (Json::Value const & response)
    {
        bool const result
            ( Json::Value ("2.0") == response["jsonrpc"]
              and response["error"].isObject ()
              and response["error"]["code"].isNumeric ()
              and response["error"]["message"].isString ()
            );
        return result;
    }

    static
    bool
    isSuccessResponse (Json::Value const & response)
    {
        bool const result
            ( Json::Value ("2.0") == response["jsonrpc"]
              and response.isMember ("result")
            );
        return result;
    }
}

namespace conveyor
{
    void
    SynchronousCallback::response (Json::Value const & response)
    {
        QMutexLocker locker (& this->m_mutex);
        this->m_value = response;
        this->m_condition.wakeAll ();
    }

    Json::Value
    SynchronousCallback::wait (void)
    {
        this->m_condition.wait (& this->m_mutex);
        return this->m_value;
    }

    Json::Value
    SynchronousCallback::invoke
        ( JsonRpc * jsonRpc
        , std::string const & methodName
        , Json::Value const & params
        )
    {
        SynchronousCallback callback;

        // Acquire the mutex. This ensures the response thread is
        // blocked until this thread has had a chance to start waiting
        // for a response
        QMutexLocker locker (& callback.m_mutex);

        // Send the request
        jsonRpc->invoke (methodName, params, & callback);

        // Start waiting for a response
        Json::Value const response (callback.wait ());

        // Handle the response
        if (isErrorResponse (response))
        {
            Json::Value const error (response["error"]);
            int const code (error["code"].asInt ());
            std::string const message (error["message"].asString ());
            Json::Value const data (error["data"]);

            fprintf(stderr,
                "Error invoking \"%s\"\n"
                "This may indicate mismatched "
                "Conveyor and MakerWare versions,\n"
                "check your Conveyor and MakerWare "
                "logs for more information.\n\n",
                methodName.c_str());

            throw JsonRpcException (methodName, params, code, message, data);
        }
        else
        if (not isSuccessResponse (response))
        {
            throw std::runtime_error("Response is not success!");
        }
        else
        {
            Json::Value const result (response["result"]);
            return result;
        }
    }
}
