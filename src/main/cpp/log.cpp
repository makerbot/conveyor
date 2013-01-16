// Copyright 2013 MakerBot Industries

#include <string>
#include <vector>

#include "conveyor/log.h"

namespace conveyor {

Log::Metadata::Metadata(const Severity p_severity,
                        const char * const p_file,
                        const char * const p_func,
                        const size_t p_line,
                        const time_t p_curTime)
    : severity(p_severity),
      file(p_file),
      func(p_func),
      line(p_line),
      curTime(p_curTime) {
}

/// The log used by Log::appendToGlobalLog and the logging macros
///
/// Initially this is set to an in-memory log. Typically the
/// application should replace the global log with a different
/// implementation that logs to disk by calling one of the
/// Log::setGlobalLog() methods.
static Log *s_globalLog(createInMemoryLog());

/// The log threshhold used by the logging macros
///
/// Initially all errors and infos are logged, but not spam.
static Log::Severity s_globalLogThreshold(Log::kInfo);

std::ostream &Log::appendToGlobalLog(const Metadata &metadata) {
    return s_globalLog->addEntry(metadata);
}

void Log::setGlobalLog(Log *log, const Flush flush) {
    if (log) {
        if (flush == kFlush)
            s_globalLog->flushLogToLog(log);
        s_globalLog = log;
    } else {
      LOG_ERROR << "Cannot set NULL log" << std::endl;
    }
}

void Log::setGlobalLogThreshold(const Severity severity) {
    s_globalLogThreshold = severity;
}

Log::Severity Log::globalLogThreshold() {
    return s_globalLogThreshold;
}

void Log::flushLogToLog(Log *) {  // NOLINT
    // Default implementation does nothing
}

Log::~Log() {
    // Empty destructor
}

/// Convert from Severity enum to a string
std::string Log::severityStr(const Log::Severity severity) {
    switch (severity) {
        case Log::kError:
            return "error";
        case Log::kInfo:
            return "info";
        case Log::kSpam:
            return "spam";
    }

    throw std::runtime_error("Invalid severity type");
}

/// Get the current time in "Day Mth DD HH:MM:SS YYYY" format
std::string Log::timeStr() {
    const time_t t(time(0));
    std::string s(ctime(&t));
    // Chop off trailing newline
    s.resize(s.size() - 1);
    return s;
}
}
