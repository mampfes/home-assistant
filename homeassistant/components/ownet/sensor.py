"""Support for oneWire sensors."""
import logging

import voluptuous as vol

from homeassistant.components.sensor import DEVICE_CLASSES, PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_PATH,
    CONF_UNIT_OF_MEASUREMENT,
    TEMP_CELSIUS,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from . import CONF_SERVER_INSTANCE, DATA_OWNET

_LOGGER = logging.getLogger(__name__)

CONF_VALUE_FORMAT = "value_format"
CONF_VALUE_FORMAT_FLOAT = "float"
CONF_VALUE_FORMAT_INT = "int"
CONF_VALUE_FORMAT_STRING = "string"
CONF_VALUE_FORMATS = [
    CONF_VALUE_FORMAT_FLOAT,
    CONF_VALUE_FORMAT_INT,
    CONF_VALUE_FORMAT_STRING,
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PATH): cv.string,
        vol.Optional(CONF_SERVER_INSTANCE, default=0): cv.positive_int,
        vol.Optional(CONF_DEVICE_CLASS, default=None): vol.Maybe(
            vol.In(DEVICE_CLASSES)
        ),
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=TEMP_CELSIUS): cv.string,
        vol.Optional(CONF_VALUE_FORMAT, default=CONF_VALUE_FORMAT_FLOAT): vol.In(
            CONF_VALUE_FORMATS
        ),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the onewire sensor."""
    devs = []

    dev = OnewireSensor(
        config,
        hass.data[DATA_OWNET][config[CONF_SERVER_INSTANCE]].get_io(config[CONF_PATH]),
    )
    devs.append(dev)

    add_entities(devs, True)


class OnewireSensor(Entity):
    """Representation of a onewire sensor."""

    def __init__(self, config, io):
        """Initialize ownet sensor."""
        self._name = config[CONF_NAME]
        self._value_format = config[CONF_VALUE_FORMAT]
        self._unit_of_measurement = (
            None
            if self._value_format == CONF_VALUE_FORMAT_STRING
            else config[CONF_UNIT_OF_MEASUREMENT]
        )
        self._device_class = config[CONF_DEVICE_CLASS]
        self._io = io
        self._available = False
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def should_poll(self):
        """Ownet always requires polling."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    def update(self):
        """Retrieve sensor state from onewire device."""
        self._available = bool(
            self._io.is_available()
        )  # is_available returns None if server is unavailable
        if not self._available:
            self._state = None
        else:
            state = self._io.read_value()
            if state is None:
                self._state = None
            elif self._value_format == CONF_VALUE_FORMAT_FLOAT:
                self._state = float(state)
            elif self._value_format == CONF_VALUE_FORMAT_INT:
                self._state = int(state)
            elif self._value_format == CONF_VALUE_FORMAT_STRING:
                self._state = state
