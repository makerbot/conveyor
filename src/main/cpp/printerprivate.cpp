// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor.h>

#include "printerprivate.h"

#include "conveyorprivate.h"

#include <stdexcept>

#include <QString>
#include <QStringList>

namespace
{
    static
    conveyor::ConnectionStatus
    connectionStatusFromString (QString const & string)
    {
        if("connected" == string)
            return conveyor::CONNECTED;
        else if("not connected" == string)
            return conveyor::NOT_CONNECTED;

        throw std::invalid_argument (string.toStdString());
    }
}

namespace conveyor
{
    PrinterPrivate::PrinterPrivate
        ( Conveyor * const conveyor
        , Printer * const printer
        , QString const & uniqueName
        )
        : m_conveyor (conveyor)
        , m_printer (printer)
        , m_uniqueName (uniqueName)
    {
        this->m_canPrint = true;
        this->m_canPrintToFile = true;
        this->m_connectionStatus = NOT_CONNECTED;
        this->m_displayName = "Dummy Printer";
        this->m_printerType = "Replicator";
        this->m_machineNames = QStringList("TheReplicator");
        this->m_numberOfToolheads = 2;
        this->m_hasHeatedPlatform = true;
    }

    void
    PrinterPrivate::updateFromJson(Json::Value const & json)
    {
        QString const uniqueName(json["uniqueName"].asCString());
        QString const displayName(json["displayName"].asCString());
        bool const canPrint(json["canPrint"].asBool());
        bool const canPrintToFile(json["canPrintToFile"].asBool());
        ConnectionStatus const connectionStatus
            ( connectionStatusFromString
                ( QString(json["connectionStatus"].asCString())));
        QString const printerType(QString(json["printerType"].asCString()));
        int const numberOfToolheads(json["numberOfToolheads"].asInt());
        bool const hasHeatedPlatform(json["hasHeatedPlatform"].asBool());
        QStringList machineNames;
        for(Json::ArrayIndex i = 0; i < json["machineNames"].size(); ++i)
        {
            machineNames << QString(json["machineNames"][i].asCString());
        }
        float buildVolumeXmin, buildVolumeYmin, buildVolumeZmin,
              buildVolumeXmax, buildVolumeYmax, buildVolumeZmax;
        if ("The Replicator Single" == printerType) {
            buildVolumeXmin = -113.5;
            buildVolumeYmin = -74;
            buildVolumeZmin = 0;
            buildVolumeXmax = 113.5;
            buildVolumeYmax = 74;
            buildVolumeZmax = 150;
        } else if ("The Replicator Dual" == printerType) {
            buildVolumeXmin = -113.5;
            buildVolumeYmin = -74;
            buildVolumeZmin = 0;
            buildVolumeXmax = 113.5;
            buildVolumeYmax = 74;
            buildVolumeZmax = 150;
        } else if ("The Replicator 2" == printerType) {
            buildVolumeXmin = 0;
            buildVolumeYmin = 0;
            buildVolumeZmin = 0;
            buildVolumeXmax = 200;
            buildVolumeYmax = 200;
            buildVolumeZmax = 150;
        } // else, BuildVolume is 0 for now

        m_uniqueName = uniqueName;
        m_displayName = displayName;
        m_machineNames = machineNames;
        m_canPrint = canPrint;
        m_canPrintToFile = canPrintToFile;
        m_connectionStatus = connectionStatus;
        m_printerType = printerType;
        m_numberOfToolheads = numberOfToolheads;
        m_hasHeatedPlatform = hasHeatedPlatform;
        m_buildVolumeXmin = buildVolumeXmin;
        m_buildVolumeYmin = buildVolumeYmin;
        m_buildVolumeZmin = buildVolumeZmin;
        m_buildVolumeXmax = buildVolumeXmax;
        m_buildVolumeYmax = buildVolumeYmax;
        m_buildVolumeZmax = buildVolumeZmax;

        // Temperature of extruder(s) and platform(s)
        if (json.isMember("temperature")) {
            const Json::Value &temperature(json["temperature"]);
            if (temperature.isMember("tools")) {
                ToolTemperature::updateFromJson(m_toolTemperature.tools,
                                                temperature["tools"]);
            }
            if (temperature.isMember("heated_platforms")) {
                ToolTemperature::updateFromJson(m_toolTemperature.heated_platforms,
                                                temperature["heated_platforms"]);
            }
        }
    }

    Job *
    PrinterPrivate::print (QString const & inputFile
                           , const SlicerConfiguration & slicer_conf
                           , QString const & material
                           , bool const skipStartEnd)
    {
        Job * const result
            ( this->m_conveyor->m_private->print
                ( this->m_printer
                , inputFile
                , slicer_conf
                , material
                , skipStartEnd
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const skipStartEnd
        , QString const & printToFileType
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->printToFile
                ( this->m_printer
                , inputFile
                , outputFile
                , slicer_conf
                , material
                , skipStartEnd
                , printToFileType
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::slice
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->slice
                ( this->m_printer
                , inputFile
                , outputFile
                , slicer_conf
                , material
                )
            );
        return result;
    }
}
