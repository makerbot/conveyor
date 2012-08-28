#ifndef EEPROMMAP_H
#define EEPROMMAP_H

#include <QString>
#include <json/value.h>
#include <jsonrpc.h>

namespace conveyor
{
    class EepromMapPrivate
    {
        public:
            EepromMapPrivate(Json::Value eepromMap){this->eepromMap = eepromMap};
            ~EepromMapPrivate(){~this->eepromMap()};

            int getInt(QString path);
            QString getString(QString path);
            void setInt(QString path, int value);
            void setString(QString path, QString value);
        private:
            Json::Value eepromMap;
    }
}
