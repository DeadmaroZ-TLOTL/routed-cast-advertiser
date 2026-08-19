"""Advertise routed Google Cast devices with mDNS."""

from __future__ import annotations

from collections.abc import Mapping
import ipaddress
import logging
from typing import Any

import voluptuous as vol
from zeroconf.asyncio import AsyncServiceInfo

from homeassistant import config_entries
from homeassistant.components import zeroconf as ha_zeroconf
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_INSTANCE,
    CONF_MODEL,
    CONF_PROPERTIES,
    CONF_SERVER,
    CONF_SERVICES,
    CONF_UUID,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    DOMAIN,
    SERVICE_TYPE,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SERVICES): vol.All(
                    cv.ensure_list,
                    [
                        vol.Schema(
                            {
                                vol.Required(CONF_HOST): cv.string,
                                vol.Required(CONF_NAME): cv.string,
                                vol.Required(CONF_UUID): cv.string,
                                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
                                vol.Optional(CONF_INSTANCE): cv.string,
                                vol.Optional(CONF_SERVER): cv.string,
                                vol.Optional(CONF_PROPERTIES, default={}): {
                                    cv.string: cv.string
                                },
                            }
                        )
                    ],
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up YAML imports."""
    hass.data.setdefault(DOMAIN, {})
    conf = config.get(DOMAIN)
    if not conf:
        return True

    for service_conf in conf[CONF_SERVICES]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=dict(service_conf),
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Cast mDNS advertisement from a config entry."""
    async_zc = await ha_zeroconf.async_get_async_instance(hass)
    conf = {**entry.data, **entry.options}
    info = _build_service_info(conf)

    # The real Cast device can already be visible on one HA interface while this
    # routed advertisement is still needed on another. Let zeroconf choose a
    # unique instance name instead of failing the entire config entry.
    await async_zc.async_register_service(info, allow_name_change=True)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "async_zc": async_zc,
        "info": info,
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _LOGGER.info(
        "Advertising Google Cast service %s at %s:%s",
        info.name,
        conf[CONF_HOST],
        conf[CONF_PORT],
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Cast mDNS advertisement."""
    stored = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not stored:
        return True

    await stored["async_zc"].async_unregister_service(stored["info"])
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _build_service_info(conf: Mapping[str, Any]) -> AsyncServiceInfo:
    """Build an mDNS Google Cast service from config."""
    host = str(conf[CONF_HOST])
    uuid = str(conf[CONF_UUID]).lower()
    uuid_no_dash = uuid.replace("-", "")
    model = str(conf[CONF_MODEL])
    model_slug = "-".join(model.split())
    instance = str(conf.get(CONF_INSTANCE) or f"{model_slug}-{uuid_no_dash}.{SERVICE_TYPE}")
    server = str(conf.get(CONF_SERVER) or f"{uuid}.local.")
    if not instance.endswith("."):
        instance = f"{instance}."
    if not server.endswith("."):
        server = f"{server}."

    properties: dict[str, str] = {
        "id": uuid_no_dash,
        "cd": uuid_no_dash.upper(),
        "rm": uuid_no_dash[:16].upper(),
        "ve": "05",
        "md": model,
        "ic": "/setup/icon.png",
        "fn": str(conf[CONF_NAME]),
        "ca": "215044",
        "st": "1",
        "bs": uuid_no_dash[:12].upper(),
        "nf": "1",
        "rs": "",
    }
    properties.update(conf.get(CONF_PROPERTIES, {}))

    return AsyncServiceInfo(
        SERVICE_TYPE,
        instance,
        port=conf[CONF_PORT],
        server=server,
        properties=properties,
        parsed_addresses=[str(ipaddress.ip_address(host))],
    )
