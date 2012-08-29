#ifndef EEPROMMAP
#define EEPROMMAP

#include <QString>
#include <QStringList>
#include <QScopedPointer>

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
            QScopedPointer <EepromMapPrivate> m_private;
    }
}
#endif
