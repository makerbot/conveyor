// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor.h>

#include "printerprivate.h"

#include <stdexcept>

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
        this->m_numberOfToolheads = 2;
        this->m_hasHeatedPlatform = true;
        this->m_jobs = conveyor->jobs();
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

        m_uniqueName = uniqueName;
        m_displayName = displayName;
        m_canPrint = canPrint;
        m_canPrintToFile = canPrintToFile;
        m_connectionStatus = connectionStatus;
        m_printerType = printerType;
        m_numberOfToolheads = numberOfToolheads;
        m_hasHeatedPlatform = hasHeatedPlatform;
    }

    Job *
    PrinterPrivate::print (QString const & inputFile
                           , const SlicerConfiguration & slicer_conf)
    {
        Job * const result
            ( this->m_conveyor->m_private->print
                ( this->m_printer
                , inputFile
                , slicer_conf
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->printToFile
                ( this->m_printer
                , inputFile
                , outputFile
                , slicer_conf
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::slice
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->slice
                ( this->m_printer
                , inputFile
                , outputFile
                , slicer_conf
                )
            );
        return result;
    }
}
