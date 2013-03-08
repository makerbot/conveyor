// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_PRINTER_H
#define CONVEYOR_PRINTER_H (1)

#include <QList>
#include <QMap>
#include <QObject>
#include <QString>
#include <QStringList>
#include <QScopedPointer>

#include <conveyor/fwd.h>

namespace Json {
    class Value;
}

namespace conveyor
{
    class SlicerConfiguration;

    enum FirmwareVersionError {
      kFirmwareVersionOK,
      kFirmwareVersionNotReceived,
      kFirmwareVersionNotInteger,
      kFirmwareVersionTooSmall
    };

    struct FirmwareVersion {
      FirmwareVersion();

      /// The major and minor values are only valid if error is
      /// kFirmwareVersionOK
      FirmwareVersionError m_error;
      int m_major;
      int m_minor;

      /// Create a version string in format of "X.Y"
      ///
      /// If m_error is not kFirmwareVersionOK, the string will be an
      /// error message instead of the version number
      QString str() const;
    };

    // XXX: not sure what type we want for this
    typedef float Temperature;

    /// See "tool-temperature" in conveyor-jsonrpc-api.md
    class ToolTemperature {
    public:
        QMap<QString, Temperature> tools;
        QMap<QString, Temperature> heated_platforms;

        static void updateFromJson(QMap<QString, Temperature> &tmap,
                                   const Json::Value &json);
    };

    class Printer : public QObject
    {
        Q_OBJECT

    public:
        enum State {
            kDisconnected,
            kBusy,
            kIdle,
            kOperation,
            kPaused,
            kInvalid
        };

        ~Printer ();

        /** A human readable name for the printer, for display in GUI elements */
        QString const & displayName () const;

        /** A name for the printer guaranteed to be distinct from all other
            printer names */
        QString const & uniqueName () const;

        /** Names a type of machine can be known by */
        QStringList const & machineNames() const;

        /** A string represenetation of the type of printer this is */
        QString const & printerType () const;

        QString profileName() const;

        State state() const;

        /** Can this printer create physical objects? false for virtual printers */
        bool canPrint () const;

        /** Can this printer print to a file? */
        bool canPrintToFile () const;

        Conveyor * conveyor ();

        /** The number of extruders the printer has. Usually 1 or 2. */
        int numberOfExtruders () const;

        /** True if this printer can set the temperature of its platform */
        bool hasHeatedPlatform () const;

        const ToolTemperature &toolTemperature () const;

        /** The available build volume */
        float buildVolumeXmin() const;
        float buildVolumeYmin() const;
        float buildVolumeZmin() const;
        float buildVolumeXmax() const;
        float buildVolumeYmax() const;
        float buildVolumeZmax() const;

        const FirmwareVersion &firmwareVersion() const;

        /** Ask the machine to move by some amount at a given speed */
        void jog (float x, float y, float z, float a, float b, float f);

        virtual Job * print (QString const & inputFile,
                             const SlicerConfiguration & slicer_conf,
                             QString const & material,
                             bool const hasStartEnd);

        virtual Job * printToFile (QString const & inputFile, QString const & outputFile,
                                   const SlicerConfiguration & slicer_conf,
                                   QString const & material,
                                   bool const hasStartEnd,
                                   QString const & printToFile);

        virtual Job * slice (QString const & inputFile, QString const & outputFile,
                             const SlicerConfiguration & slicer_conf,
                             QString const & material,
                             bool const addStartEnd);

    signals:
        void changed (void);

    private:
        Printer (Conveyor * conveyor, QString const & uniqueName);

        QScopedPointer <PrinterPrivate> m_private;

        void emitChanged (void);

        friend class Conveyor;
        friend class ConveyorPrivate;
        friend class FakePrinter;
        friend class Job;
        friend class JobPrivate;
        friend class PrinterAddedMethod;
        friend class PrinterChangedMethod;
        friend class MachineTemperatureChangedMethod;
    };
}

#endif
