#ifndef EEPROMMAP_H
#define EEPROMMAP_H

#include <QString>
#include <QStringList>
#include <QScopedPointer>
#include <QObject>

#include <conveyor/fwd.h>

#include <json/value.h>
#include <jsonrpc.h>

namespace conveyor
{
    class EepromMap
    {
    public:
        EepromMap(Json::Value eepromMap);
        ~EepromMap();

        int getInt(QString path) const;
        QString getString(QString path) const;
        void setInt(QString path, int value);
        void setString(QString path, QString value);
        Json::Value getEepromMap(void) const;
    private:
        EepromMapPrivate * const m_private;
    };
}
#endif
