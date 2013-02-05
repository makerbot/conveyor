#include "notification_methods.h"

#include "conveyor/conveyor.h"
#include "conveyor/log.h"

namespace conveyor {
PortAttachedMethod::PortAttachedMethod(Conveyor *conveyor)
    : m_conveyor(conveyor) {
}
        
Json::Value PortAttachedMethod::invoke(Json::Value const & params) {
  try {
    // Memory leak
    const Port * const port(new Port(params));
    m_conveyor->emitPortAttached(port);
  } catch(const std::exception &e) {
    LOG_ERROR << e.what() << std::endl;
  }

  return Json::Value(Json::nullValue);
}

PortDetachedMethod::PortDetachedMethod(Conveyor *conveyor)
    : m_conveyor(conveyor) {
}
        
Json::Value PortDetachedMethod::invoke(Json::Value const & params) {
  const std::string errorStr("error in params: " + params.toStyledString());

  if (params.isObject()) {
    const std::string portNameKey("port_name");
    if (params.isMember(portNameKey)) {
      const Json::Value &portName(params[portNameKey]);
      if (portName.isString()) {
        const std::string portNameStr(portName.asString());
        m_conveyor->emitPortDetached(QString::fromUtf8(portNameStr.c_str()));
      } else {
        LOG_ERROR << errorStr << std::endl;
      }
    } else {
      LOG_ERROR << errorStr << std::endl;
    }
  } else {
    LOG_ERROR << errorStr << std::endl;
  }

  return Json::Value(Json::nullValue);
}
}
