// Copyright 2013 MakerBot Industries

#include <vector>

#include "conveyor/log.h"

namespace conveyor {

/// The default log, keeps entries in memory
class InMemoryLog : public Log {
 public:
    InMemoryLog() {
    }

    ~InMemoryLog() {
        for (std::vector<Entry *>::const_iterator iter = m_entries.begin();
                 iter != m_entries.end(); ++iter) {
            delete *iter;
        }
    }

    virtual std::ostream &addEntry(const Metadata &metadata) {
        if (metadata.severity <= globalLogThreshold()) {
            Entry *entry(new Entry(metadata));
            m_entries.push_back(entry);
            return entry->stringStream;
        } else {
            return m_nullStream;
        }
    }

    virtual void flushLogToLog(Log *log) {
        for (std::vector<Entry *>::const_iterator iter = m_entries.begin();
                 iter != m_entries.end(); ++iter) {
            Entry *entry(*iter);
            log->addEntry(entry->metadata) << entry->stringStream.str();
        }
    }

 private:
    struct Entry {
        explicit Entry(const Metadata &p_metadata)
                : metadata(p_metadata) {
        }

        const Metadata metadata;
        std::ostringstream stringStream;
    };

    std::vector<Entry *> m_entries;

    NullStream m_nullStream;
};

Log *createInMemoryLog() {
    return new InMemoryLog();
}
}
