// Copyright 2013 MakerBot Industries

#ifndef CONVEYOR_LOG_H
#define CONVEYOR_LOG_H

#include <ctime>
#include <fstream>  // NOLINT(readability/streams)
#include <sstream>  // NOLINT(readability/streams)
#include <stdexcept>
#include <string>

// __PRETTY_FUNCTION__ is a GCC-specific variable that includes the
// class type signature (as opposed to __func__ which is just the
// function name).
#ifdef __GNUC__
#define LOG_METADATA_INIT(severity_) \
  conveyor::Log::Metadata(severity_, \
                          __FILE__,            \
                          __PRETTY_FUNCTION__, \
                          __LINE__, \
                          time(0))
#else
#define LOG_METADATA_INIT(severity_) \
  conveyor::Log::Metadata(severity_, \
                          __FILE__, \
                          __func__, \
                          __LINE__, \
                          time(0))
#endif

/// Log an error
#define LOG_ERROR \
    conveyor::Log::appendToGlobalLog(LOG_METADATA_INIT(conveyor::Log::kError))

/// Log debugging info
#define LOG_INFO \
    conveyor::Log::appendToGlobalLog(LOG_METADATA_INIT(conveyor::Log::kInfo))

/// Log spammy debugging info
#define LOG_SPAM \
    conveyor::Log::appendToGlobalLog(LOG_METADATA_INIT(conveyor::Log::kSpam))

namespace conveyor {

/// Logging for errors and debug info
///
/// As soon as possible in the program, the Log::setGlobalLog()
/// function should be invoked to set an on-disk logger. Any logging
/// done before this will be kept in a buffer and written out as soon
/// as the new logger is set.
///
/// An on-disk log can be created with createOnDiskLog("path/to/log"),
/// or you can subclass Log to use your own logging system.
class Log {
public:
    enum Severity {
        /// Error case, something has gone wrong
        ///
        /// Use this for any error, no matter how trivial or severe
        kError,

        /// Non-error debugging info
        ///
        /// Use this for logging interesting things like actions and paths
        kInfo,

        /// Aggressive debugging info that will spam the log
        ///
        /// Use this for logging annoying things like all communication
        /// between a client and server
        kSpam
    };

    /// Metadata for a log entry, does not include the log message itself
    struct Metadata {
        Metadata(const Severity p_severity,
                         const char * const p_file,
                         const char * const p_func,
                         const size_t p_line,
                         const time_t p_curTime);

        const Severity severity;
        const char * const file;
        const char * const func;
        const size_t line;
        const time_t curTime;
    };

    /// Used in setGlobalLog
    enum Flush {
        kFlush,
        kNoFlush
    };

    /// Do not call this directly; use LOG_ERROR, LOG_INFO, or LOG_SPAM instead
    static std::ostream &appendToGlobalLog(const Metadata &metadata);

    /// Set the log that will be used by the logging macros
    ///
    /// If flush is kFlush, in-memory entries in old global log will be
    /// written into the new global log with flushLogToLog().
    static void setGlobalLog(Log *log, const Flush flush = kFlush);

    /// Set the log level used by the logging macros
    static void setGlobalLogThreshold(const Severity severity);

    /// Get the log level used by the logging macros
    static Severity globalLogThreshold();

    /// Begin a new log entry
    ///
    /// The log message should be written to the returned output stream.
    virtual std::ostream &addEntry(const Metadata &metadata) = 0;

    /// Write out in-memory entries to another log
    ///
    /// This is used to support logging before an on-disk log file is
    /// created. The log entries can be kept in-memory until the file is
    /// created, then written out all at once.
    ///
    /// The default implementation of this method does nothing.
    virtual void flushLogToLog(Log *log);

    virtual ~Log();

protected:
    // Utilities

    /// Convert from Severity enum to a string
    static std::string severityStr(const Log::Severity severity);

    /// Get the current time in "Day Mth DD HH:MM:SS YYYY" format
    static std::string timeStr();

    /// Invalid stream that discards inputs
    struct NullStream : std::ostream {
        NullStream(): std::ios(0), std::ostream(0) {
        }
    };
};

/// Create a log that keeps entries in memory (the default log)
Log *createInMemoryLog();

/// Create a log that is written to disk
///
/// Each entry in the output will look like this:
///
///   path/to/source.cpp:31: info
///   void someCoolFunction(int param)
///   Mon Jan 14 14:14:50 2013
///   Something cool happened
Log *createOnDiskLog(const std::string &path);
}

#endif  // CONVEYOR_LOG_H
