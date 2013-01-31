// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef JOBCHANGEDMETHOD_H
#define JOBCHANGEDMETHOD_H (1)

#include <jsonrpc/jsonrpc.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    class JobChangedMethod : public JsonRpcMethod
    {
    public:
        JobChangedMethod (ConveyorPrivate * conveyorPrivate);
        ~JobChangedMethod (void);
        
        Json::Value invoke (Json::Value const & params);
        
    private:
        ConveyorPrivate * const m_conveyorPrivate;
    };
}

#endif // JOBCHANGEDMETHOD_H
