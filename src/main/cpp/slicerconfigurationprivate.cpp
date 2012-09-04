#include "slicerconfigurationprivate.h"

namespace conveyor
{

    SlicerConfiguration *
    SlicerConfigurationPrivate::defaultConfiguration(SlicerConfiguration::Quality quality)
    {
        Json::Value null;
        SlicerConfiguration * const config(new SlicerConfiguration(null));

        switch(quality)
        {
        case SlicerConfiguration::LowQuality:
            config->setSlicer(SlicerConfiguration::MiracleGrue);
            config->setLayerHeight(.3);
            break;
        case SlicerConfiguration::MediumQuality:
            config->setSlicer(SlicerConfiguration::MiracleGrue);
            break;
        case SlicerConfiguration::HighQuality:
            config->setSlicer(SlicerConfiguration::Skeinforge);
            break;
        }
        return config;
    }

    SlicerConfigurationPrivate::SlicerConfigurationPrivate(Json::Value &) :
        m_slicer(SlicerConfiguration::MiracleGrue),
        m_extruder(SlicerConfiguration::Left),
        m_raft(true),
        m_supports(false),
        m_infill(0.90),
        m_layerHeight(0.2),
        m_shells(3),
        m_extruderTemperature(220),
        m_platformTemperature(220),
        m_printSpeed(80),
        m_travelSpeed(150)
    {
        // TODO
    }

    Json::Value SlicerConfigurationPrivate::toJSON() const
    {
        Json::Value root;

        // Slicer name and min/max versions
        root["slicer"] = slicerName().toStdString();

        // TODO: rewrite the software stack, using strings
        // instead of integers to represent toolheads
        root["extruder"] = 0;

        root["raft"] = m_raft;
        root["support"] = m_supports;

        root["infill"] = m_infill;
        root["layer_height"] = m_layerHeight;
        root["shells"] = m_shells;

        root["extruder_temperature"] = m_extruderTemperature;
        root["platform_temperature"] = m_platformTemperature;

        root["travel_speed"] = m_travelSpeed;
        root["print_speed"] = m_printSpeed;

        return root;
    }

    SlicerConfiguration::Slicer SlicerConfigurationPrivate::slicer() const
    {
        return m_slicer;
    }

    QString SlicerConfigurationPrivate::slicerName() const
    {
        switch (m_slicer) {
        case SlicerConfiguration::Skeinforge:
            return "Skeinforge";
        case SlicerConfiguration::MiracleGrue:
            return "MiracleGrue";
        default:
            return QString();
        }
    }

    SlicerConfiguration::Extruder SlicerConfigurationPrivate::extruder() const
    {
        return m_extruder;
    }

    QString SlicerConfigurationPrivate::extruderName() const
    {
        switch (m_extruder) {
        case SlicerConfiguration::Left:
            return "Left";
        case SlicerConfiguration::Right:
            return "Right";
        default:
            return QString();
        }
    }

    bool SlicerConfigurationPrivate::raft() const
    {
        return m_raft;
    }

    bool SlicerConfigurationPrivate::supports() const
    {
        return m_supports;
    }

    double SlicerConfigurationPrivate::infill() const
    {
        return m_infill;
    }

    double SlicerConfigurationPrivate::layerHeight() const
    {
        return m_layerHeight;
    }

    unsigned SlicerConfigurationPrivate::shells() const
    {
        return m_shells;
    }

    unsigned SlicerConfigurationPrivate::extruderTemperature() const
    {
        return m_extruderTemperature;
    }

    unsigned SlicerConfigurationPrivate::platformTemperature() const
    {
        return m_platformTemperature;
    }

    unsigned SlicerConfigurationPrivate::printSpeed() const
    {
        return m_printSpeed;
    }

    unsigned SlicerConfigurationPrivate::travelSpeed() const
    {
        return m_travelSpeed;
    }

    void SlicerConfigurationPrivate::setSlicer(SlicerConfiguration::Slicer slicer)
    {
        m_slicer = slicer;
    }

    void SlicerConfigurationPrivate::setExtruder(SlicerConfiguration::Extruder extruder)
    {
        m_extruder = extruder;
    }

    void SlicerConfigurationPrivate::setRaft(bool raft)
    {
        m_raft = raft;
    }

    void SlicerConfigurationPrivate::setSupports(bool supports)
    {
        m_supports = supports;
    }

    void SlicerConfigurationPrivate::setInfill(double infill)
    {
        m_infill = infill;
    }

    void SlicerConfigurationPrivate::setLayerHeight(double height)
    {
        m_layerHeight = height;
    }

    void SlicerConfigurationPrivate::setShells(unsigned shells)
    {
        m_shells = shells;
    }

    void SlicerConfigurationPrivate::setExtruderTemperature(unsigned temperature)
    {
        m_extruderTemperature = temperature;
    }

    void SlicerConfigurationPrivate::setPlatformTemperature(unsigned temperature)
    {
        m_platformTemperature = temperature;
    }

    void SlicerConfigurationPrivate::setPrintSpeed(unsigned speed)
    {
        m_printSpeed = speed;
    }

    void SlicerConfigurationPrivate::setTravelSpeed(unsigned speed)
    {
        m_travelSpeed = speed;
    }
}
