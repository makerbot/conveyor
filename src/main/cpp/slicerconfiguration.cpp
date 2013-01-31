#include <conveyor/conveyor.h>

#include <conveyor/slicers.h>

#include "slicerconfigurationprivate.h"

namespace conveyor
{

    SlicerConfiguration *
    SlicerConfiguration::defaultConfiguration(Preset preset)
    {
        return SlicerConfigurationPrivate::defaultConfiguration(preset);
    }

    SlicerConfiguration::SlicerConfiguration(Json::Value &json)
        : m_private(new SlicerConfigurationPrivate(json))
    {
    }

    Json::Value
    SlicerConfiguration::toJSON() const
    {
        return m_private->toJSON();
    }

    SlicerConfiguration::Slicer
    SlicerConfiguration::slicer() const
    {
        return m_private->slicer();
    }

    QString
    SlicerConfiguration::slicerName() const
    {
        return m_private->slicerName();
    }

    SlicerConfiguration::Extruder
    SlicerConfiguration::extruder() const
    {
        return m_private->extruder();
    }

    bool
    SlicerConfiguration::raft() const
    {
        return m_private->raft();
    }

    bool
    SlicerConfiguration::supports() const
    {
        return m_private->supports();
    }

    double
    SlicerConfiguration::infill() const
    {
        return m_private->infill();
    }

    double
    SlicerConfiguration::layerHeight() const
    {
        return m_private->layerHeight();
    }

    unsigned
    SlicerConfiguration::shells() const
    {
        return m_private->shells();
    }

    unsigned
    SlicerConfiguration::extruderTemperature() const
    {
        return m_private->extruderTemperature();
    }

    unsigned
    SlicerConfiguration::platformTemperature() const
    {
        return m_private->platformTemperature();
    }

    unsigned
    SlicerConfiguration::printSpeed() const
    {
        return m_private->printSpeed();
    }

    unsigned
    SlicerConfiguration::travelSpeed() const
    {
        return m_private->travelSpeed();
    }

    void
    SlicerConfiguration::setSlicer(Slicer slicer)
    {
        m_private->setSlicer(slicer);
    }

    void
    SlicerConfiguration::setExtruder(Extruder extruder)
    {
        m_private->setExtruder(extruder);
    }

    void
    SlicerConfiguration::setRaft(bool raft)
    {
        return m_private->setRaft(raft);
    }

    void
    SlicerConfiguration::setSupports(bool supports)
    {
        m_private->setSupports(supports);
    }

    void
    SlicerConfiguration::setInfill(double infill)
    {
        m_private->setInfill(infill);
    }

    void
    SlicerConfiguration::setLayerHeight(double height)
    {
        m_private->setLayerHeight(height);
    }

    void
    SlicerConfiguration::setShells(unsigned shells)
    {
        m_private->setShells(shells);
    }

    void
    SlicerConfiguration::setExtruderTemperature(unsigned temperature)
    {
        m_private->setExtruderTemperature(temperature);
    }

    void
    SlicerConfiguration::setPlatformTemperature(unsigned temperature)
    {
        m_private->setPlatformTemperature(temperature);
    }

    void
    SlicerConfiguration::setPrintSpeed(unsigned speed)
    {
        m_private->setPrintSpeed(speed);
    }

    void
    SlicerConfiguration::setTravelSpeed(unsigned speed)
    {
        m_private->setTravelSpeed(speed);
    }

    void
    SlicerConfiguration::setProfilePath(const QString &path)
    {
        m_private->setProfilePath(path);
    }
}
