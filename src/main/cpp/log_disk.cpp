// Copyright 2013 MakerBot Industries

#include <string>

#include "conveyor/log.h"

namespace conveyor {

/// A log that is written to disk
class OnDiskLog : public Log {
 public:
    explicit OnDiskLog(const std::string &path)
        throw(std::runtime_error) {
        m_fileStream.open(path.c_str());
        if (m_fileStream.fail()) {
            throw std::runtime_error("Failed to open log file " + path);
        }
    }

    /// Start a new log entry
    ///
    /// The first line contains the file, line number, and severity
    /// The second line contains the date/time and the function
    virtual std::ostream &addEntry(const Metadata &metadata) {
        if (metadata.severity <= globalLogThreshold()) {
            m_fileStream
                    << std::endl
                    << metadata.file << ":" << metadata.line
                    << ": " << severityStr(metadata.severity)
                    << std::endl
                    << metadata.func
                    << std::endl
                    << timeStr()
                    << std::endl;

            return m_fileStream;
        } else {
            return m_nullStream;
        }
    }

 private:
    std::ofstream Log::m_fileStream;
    NullStream m_nullStream;
};

Log *createOnDiskLog(const std::string &path) {
    return new OnDiskLog(path);
}
}
