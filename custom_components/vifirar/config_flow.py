"""Config flow: sajtadress + API-nyckel, validerad mot sajtens ping-endpoint.

Två flöden delar samma validering:

- `user`: första gången sajten läggs till.
- `reauth`: när nyckeln slutat gälla. Den vägen SAKNADES tidigare, och det var integrationens
  största svaghet i drift. Ägaren kan när som helst byta eller återkalla API-nyckeln i sajtens
  Inställningar, och då börjar `_async_update_data` kasta ConfigEntryAuthFailed. Home Assistant
  visar då "Reparation krävs" - men utan ett reauth-steg fanns ingen ruta att skriva den nya
  nyckeln i, så enda utvägen var att ta bort integrationen och lägga till den igen. Med det
  förlorades entitets-id:n och därmed varje automation och historikgraf som pekade på dem.
"""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_URL, DOMAIN, PING_PATH

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_API_KEY): str,
    }
)

# Reauth: adressen är redan känd och ska inte skrivas om - bara nyckeln byts.
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})

TIMEOUT_SECONDS = 15

# Sajternas hem. Används bara för att fylla i åt den som skriver enbart sajtnamnet - en egen domän
# skrivs ut i sin helhet och rörs aldrig.
PLATTFORMSDOMAN = "vifirar.se"

# Visas i formularets beskrivning via description_placeholders (se async_step_user). hassfest
# tillåter inte URL:er i språkfilerna, därför en placeholder och inte en sträng i strings.json.
EXEMPEL_ADRESS = "karl-och-sara"


def _normalize_url(raw: str) -> tuple[str, str | None]:
    """Returnerar (url, felkod).

    Adressen är det som ROUTAR anropet: nyckeln bor i sajtens egen databas och går inte att slå upp
    utan att veta vilken sajt det gäller. Den kan alltså inte utgå - men den ska tåla att skrivas
    som man tänker på den. Alla tre formerna nedan ger samma sak:

        carl-och-julia
        carl-och-julia.vifirar.se
        https://carl-och-julia.vifirar.se

    Den första var tidigare en fälla: den blev "https://carl-och-julia", ett värdnamn som inte finns,
    och felet såg ut som en trasig nyckel. Egna domäner (som innehåller en punkt) rörs inte.
    """
    url = (raw or "").strip().rstrip("/")
    if url.startswith("http://"):
        # API-nyckeln skickas som Bearer-token i klartext over http:// - varna i stallet
        # for att tyst acceptera och lacka nyckeln till varje natverk pa vagen.
        return url, "insecure_url"
    host = url[len("https://"):] if url.startswith("https://") else url
    if host and "." not in host.split("/")[0]:
        host = f"{host}.{PLATTFORMSDOMAN}"
    return "https://" + host, None


class VifirarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Två fält, ett anrop, klart."""

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_url: str | None = None

    async def _ping(self, url: str, api_key: str) -> tuple[dict[str, Any] | None, str | None]:
        """Ett anrop mot sajtens ping-endpoint. Returnerar (info, felkod)."""
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(TIMEOUT_SECONDS):
                resp = await session.get(
                    url + PING_PATH, headers={"Authorization": f"Bearer {api_key}"}
                )
                if resp.status == 401:
                    return None, "invalid_auth"
                if resp.status != 200:
                    return None, "cannot_connect"
                return await resp.json(), None
        except (aiohttp.ClientError, TimeoutError):
            return None, "cannot_connect"

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url, url_error = _normalize_url(user_input[CONF_URL])
            if url_error:
                errors["base"] = url_error
            else:
                api_key = user_input[CONF_API_KEY].strip()
                info, error = await self._ping(url, api_key)
                if error:
                    errors["base"] = error
                else:
                    await self.async_set_unique_id(info.get("slug") or url)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=info.get("title") or url,
                        data={CONF_URL: url, CONF_API_KEY: api_key},
                    )
        # hassfest tillater inte URL:er i sprakfilerna - exemplet skickas darfor in som en
        # placeholder i stallet for att sta i strangen.
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={"exempel": EXEMPEL_ADRESS},
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Nyckeln slutade gälla. Adressen behålls; bara nyckeln ska skrivas om."""
        self._reauth_url = entry_data.get(CONF_URL)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        url = self._reauth_url or (entry.data.get(CONF_URL) if entry else None)
        if user_input is not None and url:
            api_key = user_input[CONF_API_KEY].strip()
            info, error = await self._ping(url, api_key)
            if error:
                errors["base"] = error
            else:
                # Samma entry uppdateras, alltså behålls entitets-id:n - och därmed automationerna
                # och historiken. Det är hela poängen med reauth i stället för "ta bort och lägg
                # till igen".
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, CONF_API_KEY: api_key}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
            description_placeholders={"url": url or ""},
        )
