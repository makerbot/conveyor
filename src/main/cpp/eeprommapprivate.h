#ifndef EEPROMMAPPRIVATE_H
#define EEPROMMAPPRIVATE_H

#include <QString>
#include <QStringList>
#include <vector>

#include <json/value.h>

namespace conveyor
{

    class EepromMapPrivateTestCase;

    class EepromMapPrivate
    {
        public:
            EepromMapPrivate(Json::Value eepromMap);
            ~EepromMapPrivate(void);
            EepromMapPrivate (EepromMapPrivate & other);
            EepromMapPrivate & operator= (EepromMapPrivate & other);
            EepromMapPrivate & operator= (EepromMapPrivate other);

            std::vector<int> * getInts(QString path);
        	std::vector<float> * getFloats(QString path);
            std::vector<QString> * getStrings(QString path);
            void setInts(QString path, std::vector<int> value);
        	void setFloats(QString path, std::vector<float> value);
            void setStrings(QString path, std::vector<QString> value);

            Json::Value getEepromMap(void) ;

        private:
            QString m_mainMap;
            Json::Value m_eepromMap;
            QStringList splitPath(QString path) ;
            Json::Value * getEntry(QStringList path);

            friend class EepromMapPrivateTestCase;

    };
}
#endif
