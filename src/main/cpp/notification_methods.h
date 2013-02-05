#ifndef NOTIFICATION_METHODS_H_
#define NOTIFICATION_METHODS_H_

#include "jsonrpc/jsonrpc.h"

namespace Json {
class Value;
}

namespace conveyor {

class Conveyor;

class PortAttachedMethod : public JsonRpcMethod {
 public:
  PortAttachedMethod(Conveyor *conveyor);
        
  Json::Value invoke (Json::Value const & params);

 private:
  Conveyor * const m_conveyor;
};

class PortDetachedMethod : public JsonRpcMethod {
 public:
  PortDetachedMethod(Conveyor *conveyor);
        
  Json::Value invoke (Json::Value const & params);

 private:
  Conveyor * const m_conveyor;
};
}

#endif  // NOTIFICATION_METHODS_H_
