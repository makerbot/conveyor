// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef PRINTERADDEDMETHOD_H
#define PRINTERADDEDMETHOD_H (1)

#include <jsonrpc/jsonrpc.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    class PrinterAddedMethod : public JsonRpcMethod
    {
    public:
        PrinterAddedMethod (ConveyorPrivate * conveyorPrivate);
        ~PrinterAddedMethod (void);
        
        Json::Value invoke (Json::Value const & params);
        
    private:
        ConveyorPrivate * const m_conveyorPrivate;
    };
}

#endif // PRINTERADDEDMETHOD_H
