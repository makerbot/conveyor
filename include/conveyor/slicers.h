// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SLICERS_H
#define SLICERS_H

#include <QObject>
#include <QString>

#include <json/value.h>

namespace conveyor
{
    /**
       Settings for the Skeinforge and MiracleGrue slicers
     */
    class SlicerConfiguration : public QObject
    {
        Q_OBJECT

    public:
        enum Slicer {
            Skeinforge,
            MiracleGrue
        };

        enum Quality {
            LowQuality,
            MediumQuality,
            HighQuality
        };

        enum Extruder {
            Left,
            Right
        };

        // TODO:
        static SlicerConfiguration *miracleGrueDefaults(Quality quality);
        static SlicerConfiguration *skeinforgeGrueDefaults(Quality quality);

        /// Unpack a configuration serialized to JSON
        SlicerConfiguration(const QString &);

        /// Serialize configuration as JSON
        Json::Value toJSON() const;

        Slicer slicer() const;
        QString slicerName() const;

        Extruder extruder() const;
        QString extruderName() const;

        bool raft() const;
        bool supports() const;

        double infill() const;
        double layerHeight() const;
        unsigned shells() const;

        unsigned extruderTemperature() const;
        unsigned platformTemperature() const;

        unsigned printSpeed() const;
        unsigned travelSpeed() const;

    public slots:
        void setSlicer(Slicer slicer);
        void setExtruder(Extruder extruder);

        void setRaft(bool raft);
        void setSupports(bool supports);

        void setInfill(double infill);
        void setLayerHeight(double height);
        void setShells(unsigned shells);

        void setExtruderTemperature(unsigned temperature);
        void setPlatformTemperature(unsigned temperature);

        void setPrintSpeed(unsigned speed);
        void setTravelSpeed(unsigned speed);

    private:
        Slicer m_slicer;
        Extruder m_extruder;

        bool m_raft;
        bool m_supports;

        double m_infill;
        double m_layerHeight;
        unsigned m_shells;

        unsigned m_extruderTemperature;
        unsigned m_platformTemperature;

        unsigned m_printSpeed;
        unsigned m_travelSpeed;
    };
}

#endif
