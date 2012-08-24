// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef JOBREMOVEDMETHOD_H
#define JOBREMOVEDMETHOD_H (1)

#include <jsonrpc.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    class JobRemovedMethod : public JsonRpcMethod
    {
    public:
        JobRemovedMethod (ConveyorPrivate * conveyorPrivate);
        ~JobRemovedMethod (void);
        
        Json::Value invoke (Json::Value const & params);
        
    private:
        ConveyorPrivate * const m_conveyorPrivate;
    };
}

#endif // JOBREMOVEDMETHOD_H
