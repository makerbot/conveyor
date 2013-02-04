// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef PRINTERCHANGEDMETHOD_H
#define PRINTERCHANGEDMETHOD_H (1)

#include <jsonrpc/jsonrpc.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    class PrinterChangedMethod : public JsonRpcMethod
    {
    public:
        PrinterChangedMethod (ConveyorPrivate * conveyorPrivate);
        ~PrinterChangedMethod (void);
        
        Json::Value invoke (Json::Value const & params);
        
    private:
        ConveyorPrivate * const m_conveyorPrivate;
    };
}

#endif // PRINTERCHANGEDMETHOD_H
