// Copyright 2013 Makerbot Industries

#include "conveyor/port.h"
#include <jsoncpp/json/json.h>

#include <stdexcept>

namespace conveyor {

Port::Port(const std::string &name,
     const std::string &label,
     const int vid,
     const int pid)
    : m_name(name),
      m_label(label),
      m_vid(vid),
      m_pid(pid) {
}

static std::string extractString(const Json::Value &json,
                             const std::string &key) {
  if (json.isObject()) {
    if (json[key].isString()) {
      return json[key].asString();
    } else {
      throw std::runtime_error("extractString failed, value not a string");
    }
  } else {
    throw std::runtime_error("extractString failed, json not an object");
  }
}

static int extractInt(const Json::Value &json,
                      const std::string &key) {
  if (json.isObject()) {
    if (json[key].isInt()) {
      return json[key].asInt();
    } else {
      throw std::runtime_error("extractInt failed, value not an int");
    }
  } else {
    throw std::runtime_error("extractInt failed, json not an object");
  }
}

Port::Port(const Json::Value &json)
    : m_name(extractString(json, "name")),
      m_label(extractString(json, "label")),
      m_vid(extractInt(json, "vid")),
      m_pid(extractInt(json, "pid")) {
}
}
