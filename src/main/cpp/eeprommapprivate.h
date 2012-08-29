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

            int getInt(QString path) const;
            QString getString(QString path) const;

            void setInt(QString path, int value);
            void setString(QString path, QString value);
          
            Json::Value getEepromMap(void) const;

        private:
            Json::Value eepromMap;
            QStringList splitPath(QString path) const;
            Json::Value getSubMap(QStringList path) const;
    }
}
#endif
