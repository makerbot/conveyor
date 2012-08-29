#ifndef EEPROMMAP_H
#define EEPROMMAP_H

#include <QString>
#include <QStringList>
#include <json/value.h>
#include <jsonrpc.h>

namespace conveyor
{
    class EepromMapPrivate
    {
        public:
            EepromMapPrivate(Json::Value eepromMap);
            ~EepromMapPrivate(void);

            int getInt(QString path);
            QString getString(QString path);

            void setInt(QString path, int value);
            void setString(QString path, QString value);
        private:
            Json::Value eepromMap;
            QStringList splitPath(QString path);
            Json::Value getSubMap(QStringList path);
    }
}
#endif
