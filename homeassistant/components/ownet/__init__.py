"""The onewire over ownet component."""

import logging

from pyownet import protocol
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PORT
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ownet"
DATA_OWNET = "data_ownet"

SEPARATOR = "/"

CONF_SERVERS = "servers"
CONF_SERVER_INSTANCE = "server"

SERVER_CONFIG = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=4304): cv.port,
    },
    extra=vol.ALLOW_EXTRA,
)
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_SERVERS): vol.All(cv.ensure_list, [SERVER_CONFIG])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up the component."""
    servers = []
    for server in config[DOMAIN][CONF_SERVERS]:
        servers.append(OwnetServer(hass, server))
    hass.data[DATA_OWNET] = servers
    return True


class OwnetServer:
    """Representation of a onewire server."""

    def __init__(self, hass, config):
        """Initialize class."""
        self._proxy = protocol.proxy(config[CONF_HOST], config[CONF_PORT])

    def get_io(self, path):
        """Get server connection specific io instance."""
        return OwnetIO(self._proxy, path)


class OwnetIO:
    """Abstraction of io to/from onewire devices. Using ownet here."""

    def __init__(self, proxy, path):
        """Initialize class."""
        self._proxy = proxy
        self._path = path  # ownet path, e.g. /10.123456789012/temperature

    def is_available(self):
        """Test if device is available."""
        if self._proxy:
            try:
                return self._proxy.present(self._path)
            except protocol.Error as exc:
                _LOGGER.error(f"ownet::protocol::present({self._path}) failed: {exc}")
        return None

    def read_value(self):
        """Read a value from from a device over owserver."""
        if self._proxy:
            try:
                return self._proxy.read(self._path).decode().lstrip()
            except protocol.Error as exc:
                _LOGGER.error(f"ownet::protocol::read({self._path}) failed: {exc}")
        return None

    def write_value(self, value):
        """Write a value to a device over owserver."""
        if self._proxy:
            try:
                self._proxy.write(self._path, value)
            except protocol.Error as exc:
                _LOGGER.error(f"ownet::protocol::write({self._path}) failed: {exc}")
