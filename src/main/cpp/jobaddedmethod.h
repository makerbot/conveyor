// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef JOBADDEDMETHOD_H
#define JOBADDEDMETHOD_H (1)

#include <jsonrpc/jsonrpc.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    class JobAddedMethod : public JsonRpcMethod
    {
    public:
        JobAddedMethod (ConveyorPrivate * conveyorPrivate);
        ~JobAddedMethod (void);
        
        Json::Value invoke (Json::Value const & params);
        
    private:
        ConveyorPrivate * const m_conveyorPrivate;
    };
}

#endif // JOBADDEDMETHOD_H
