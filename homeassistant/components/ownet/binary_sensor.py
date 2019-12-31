"""Support for oneWire binary sensors."""
import logging

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_WINDOW,
    DEVICE_CLASSES,
    PLATFORM_SCHEMA,
    BinarySensorDevice,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_PATH
import homeassistant.helpers.config_validation as cv

from . import CONF_SERVER_INSTANCE, DATA_OWNET, SEPARATOR

_LOGGER = logging.getLogger(__name__)


CONF_INVERT = "invert"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PATH): cv.string,
        vol.Optional(CONF_SERVER_INSTANCE, default=0): cv.positive_int,
        vol.Optional(CONF_DEVICE_CLASS, default=DEVICE_CLASS_WINDOW): vol.In(
            DEVICE_CLASSES
        ),
        vol.Optional(CONF_INVERT, default=False): cv.boolean,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the onewire binary sensor."""
    devs = []

    elements = config[CONF_PATH].split(SEPARATOR)
    if elements[-1] == "present":
        # if the path ends with 'present' we don't want an ordinary binary
        # sensor but a sensor which gets its value from the presence info
        path = SEPARATOR.join(elements[:-1])
        dev = OwPresenceSensor(
            config, hass.data[DATA_OWNET][config[CONF_SERVER_INSTANCE]].get_io(path)
        )
    else:
        dev = OwBinarySensor(
            config,
            hass.data[DATA_OWNET][config[CONF_SERVER_INSTANCE]].get_io(
                config[CONF_PATH]
            ),
        )
    devs.append(dev)

    add_entities(devs, True)


class OwBinarySensorBase(BinarySensorDevice):
    """Base class of a onewire binary sensor."""

    def __init__(self, config, io):
        """Initialize ownet sensor."""
        self._name = config[CONF_NAME]
        self._device_class = config[CONF_DEVICE_CLASS]
        self._invert = config[CONF_INVERT]
        self._io = io
        self._available = False
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """Ownet always requires polling."""
        return True

    @property
    def available(self):
        """Return True if entity is present on the onewire network."""
        return self._available

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._state

    def set_state(self, state):
        """Set state of binary sensor."""
        self._state = not state if self._invert else state


class OwBinarySensor(OwBinarySensorBase):
    """Representation of a binary sensor which gets its value from a onewire device."""

    def update(self):
        """Update availablity and state of the entity from the onewire network."""
        self._available = bool(
            self._io.is_available()
        )  # is_available returns None if server is unavailable
        if self._available:
            self.set_state(bool(int(self._io.read_value().decode())))
        else:
            self._state = False


class OwPresenceSensor(OwBinarySensorBase):
    """Representaton of a binary sensor which gets its value from the presence of a onewire device, e.g. iButton or silicon serial number like DS2401."""

    def update(self):
        """Update state of the entity with the presence of the entity on the onewire network."""
        state = self._io.is_available()
        if state is None:
            self._available = False
        else:
            self._available = True
            self.set_state(state)
