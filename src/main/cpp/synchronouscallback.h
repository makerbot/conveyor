// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SYNCHRONOUS_CALLBACK_H
#define SYNCHRONOUS_CALLBACK_H (1)

#include <QMutex>
#include <QWaitCondition>
#include <string>

#include <jsoncpp/json/value.h>
#include <jsonrpc/jsonrpc.h>

namespace conveyor
{
    class SynchronousCallback : public JsonRpcCallback
    {
    public:
        void response (Json::Value const & response);
        Json::Value wait (void);

        static Json::Value invoke
            ( JsonRpc * jsonRpc
            , std::string const & methodName
            , Json::Value const & params
            );

    private:
        QMutex m_mutex;
        QWaitCondition m_condition;
        Json::Value m_value;
    };
}

#endif
