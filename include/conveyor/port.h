// Copyright 2013 Makerbot Industries

#ifndef CONVEYOR_PORT_H_
#define CONVEYOR_PORT_H_

#include <string>

namespace Json {
    class Value;
}

namespace conveyor {
struct Port {
  Port(const std::string &name,
       const std::string &label,
       const int vid,
       const int pid);

  Port(const Json::Value &json);

  // TODO(nicholasbishop): not quite sure what all this field is. On
  // my system I see path like "/dev/ttyACM0", but I imagine it looks
  // a bit different on Windows. If this is just a path, let's rename
  // the field to "path".
  const std::string m_name;

  // TODO(nicholasbishop): not sure what this one is either. Archetype
  // name?
  const std::string m_label;

  /// Vender ID
  const int m_vid;

  /// Product ID
  const int m_pid;
};
}

#endif
