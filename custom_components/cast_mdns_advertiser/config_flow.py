"""Config flow for Cast mDNS Advertiser."""

from __future__ import annotations

from collections.abc import Mapping
import ipaddress
from typing import Any
import uuid as uuid_lib

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from .const import (
    CONF_BOOTSTRAP,
    CONF_INSTANCE,
    CONF_MODEL,
    CONF_PROPERTIES,
    CONF_SERVER,
    CONF_UUID,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    DOMAIN,
)


def _defaults(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return defaults for the user/options form."""
    config = config or {}
    properties = dict(config.get(CONF_PROPERTIES, {}))
    return {
        CONF_NAME: config.get(CONF_NAME, ""),
        CONF_HOST: config.get(CONF_HOST, ""),
        CONF_PORT: config.get(CONF_PORT, DEFAULT_PORT),
        CONF_UUID: config.get(CONF_UUID, ""),
        CONF_MODEL: config.get(CONF_MODEL, DEFAULT_MODEL),
        CONF_INSTANCE: config.get(CONF_INSTANCE, ""),
        CONF_SERVER: config.get(CONF_SERVER, ""),
        CONF_BOOTSTRAP: properties.get(CONF_BOOTSTRAP, ""),
    }


def _schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Build a config form schema."""
    data = _defaults(defaults)
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data[CONF_NAME]): str,
            vol.Required(CONF_HOST, default=data[CONF_HOST]): str,
            vol.Required(CONF_PORT, default=data[CONF_PORT]): int,
            vol.Required(CONF_UUID, default=data[CONF_UUID]): str,
            vol.Optional(CONF_MODEL, default=data[CONF_MODEL]): str,
            vol.Optional(CONF_INSTANCE, default=data[CONF_INSTANCE]): str,
            vol.Optional(CONF_SERVER, default=data[CONF_SERVER]): str,
            vol.Optional(CONF_BOOTSTRAP, default=data[CONF_BOOTSTRAP]): str,
        }
    )


def _normalize(user_input: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize config flow input."""
    data = dict(user_input)
    data[CONF_HOST] = str(ipaddress.ip_address(str(data[CONF_HOST]).strip()))
    data[CONF_PORT] = int(data.get(CONF_PORT, DEFAULT_PORT))

    cast_uuid = str(uuid_lib.UUID(str(data[CONF_UUID]).strip())).lower()
    data[CONF_UUID] = cast_uuid

    data[CONF_NAME] = str(data[CONF_NAME]).strip()
    data[CONF_MODEL] = str(data.get(CONF_MODEL) or DEFAULT_MODEL).strip()

    for key in (CONF_INSTANCE, CONF_SERVER):
        value = str(data.get(key, "")).strip()
        if value:
            data[key] = value
        else:
            data.pop(key, None)

    properties = dict(data.get(CONF_PROPERTIES, {}))
    bootstrap = str(data.pop(CONF_BOOTSTRAP, "")).strip()
    if bootstrap:
        properties[CONF_BOOTSTRAP] = bootstrap
    if properties:
        data[CONF_PROPERTIES] = properties
    else:
        data.pop(CONF_PROPERTIES, None)

    return data


class CastMdnsAdvertiserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cast mDNS Advertiser."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                data = _normalize(user_input)
            except ValueError:
                errors["base"] = "invalid_input"
            else:
                await self.async_set_unique_id(data[CONF_UUID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    async def async_step_import(
        self, user_input: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Import YAML configuration."""
        data = _normalize(user_input)
        await self.async_set_unique_id(data[CONF_UUID])
        self._abort_if_unique_id_configured(updates=data)
        return self.async_create_entry(title=data[CONF_NAME], data=data)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CastMdnsAdvertiserOptionsFlow:
        """Return the options flow."""
        return CastMdnsAdvertiserOptionsFlow(config_entry)


class CastMdnsAdvertiserOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Cast mDNS Advertiser."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                data = _normalize(user_input)
            except ValueError:
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(current),
            errors=errors,
        )
