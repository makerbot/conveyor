// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QMutex>
#include <QMutexLocker>
#include <QWaitCondition>
#include <stdexcept>
#include <string>

#include <json/value.h>
#include <jsonrpc.h>

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
        QMutexLocker locker (& this->m_mutex);
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
        jsonRpc->invoke (methodName, params, & callback);
        Json::Value const response (callback.wait ());
        if (isErrorResponse (response))
        {
            Json::Value const error (response["error"]);
            int const code (error["code"].asInt ());
            std::string const message (error["code"].asString ());
            Json::Value const data (error["data"]);
            throw JsonRpcException (code, message, data);
        }
        else
        if (not isSuccessResponse (response))
        {
            throw std::exception ();
        }
        else
        {
            Json::Value const result (response["result"]);
            return result;
        }
    }
}
