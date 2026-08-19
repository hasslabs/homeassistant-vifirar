"""Sensorer: OSA-räkningar, önskelista, foton och nedräkning."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class VifirarSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] = None


SENSORS: tuple[VifirarSensorDescription, ...] = (
    VifirarSensorDescription(
        key="attending", translation_key="attending", name="Kommer",
        icon="mdi:account-check", value_fn=lambda d: d["rsvp"]["attending"],
    ),
    VifirarSensorDescription(
        key="not_attending", translation_key="not_attending", name="Kommer inte",
        icon="mdi:account-off", value_fn=lambda d: d["rsvp"]["not_attending"],
    ),
    VifirarSensorDescription(
        key="responses", translation_key="responses", name="OSA-svar",
        icon="mdi:email-check", value_fn=lambda d: d["rsvp"]["responses"],
    ),
    VifirarSensorDescription(
        key="adults", translation_key="adults", name="Vuxna",
        icon="mdi:account-group", value_fn=lambda d: d["rsvp"]["adults"],
    ),
    VifirarSensorDescription(
        key="children", translation_key="children", name="Barn",
        icon="mdi:human-child", value_fn=lambda d: d["rsvp"]["children"],
    ),
    VifirarSensorDescription(
        key="wishlist_items", translation_key="wishlist_items", name="Önskelista poster",
        icon="mdi:gift-outline", value_fn=lambda d: d["wishlist"]["items"],
    ),
    VifirarSensorDescription(
        key="wishlist_reserved", translation_key="wishlist_reserved", name="Önskelista bokade",
        icon="mdi:gift", value_fn=lambda d: d["wishlist"]["reserved"],
    ),
    VifirarSensorDescription(
        key="photos", translation_key="photos", name="Gästfoton",
        icon="mdi:camera", value_fn=lambda d: d["photos"]["count"],
    ),
    VifirarSensorDescription(
        key="days_until_event", translation_key="days_until_event", name="Dagar kvar",
        icon="mdi:calendar-heart", value_fn=lambda d: d["site"]["days_until_event"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VifirarSensor(coordinator, entry, desc) for desc in SENSORS)


class VifirarSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, description: VifirarSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        site = (coordinator.data or {}).get("site", {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=site.get("title") or "Vi firar",
            manufacturer="Vi firar",
            model="Eventsajt",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=entry.data.get("url"),
        )

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            return self.entity_description.value_fn(data)
        except (KeyError, TypeError):
            return None
