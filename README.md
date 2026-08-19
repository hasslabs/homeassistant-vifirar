# Vi firar - Home Assistant-integration

Custom component som visar din [Vi firar](https://vifirar.se)-sajt som sensorer i Home Assistant:
OSA-svar (kommer/kommer inte/vuxna/barn), önskelistans bokningar, antal gästfoton och nedräkning
till eventet. Sajtens läs-API pollas var 5:e minut med en API-nyckel.

Integrationen läser bara **räkningar**. Namn, e-postadresser, allergier och meddelanden lämnar
aldrig sajten - se [Vad som skickas](#vad-som-skickas) nedan.

## Först: skapa en API-nyckel

1. Logga in på din sajt och gå till **Planering & gäster → Inställningar → Home Assistant**.
2. Klicka **Skapa API-nyckel** och kopiera nyckeln.

Nyckeln ger läsåtkomst till sajtens räkningar. Håll den hemlig, och återkalla den i samma vy om
den kommer på villovägar.

## Installation via HACS (rekommenderas)

HACS håller integrationen uppdaterad åt dig. Repot ligger inte i HACS default-butik, så det läggs
till som ett **custom repository** - en engångssak:

1. Öppna **HACS** i Home Assistant.
2. Menyn uppe till höger (tre prickar) → **Custom repositories**.
3. Klistra in repots adress, välj typen **Integration**, och klicka **Add**.
4. Sök på **Vi firar** i HACS, öppna den och klicka **Download**.
5. Starta om Home Assistant.
6. **Inställningar → Enheter & tjänster → + Lägg till integration**, sök på **Vi firar**.
7. Ange sajtens adress (t.ex. `https://karl-och-sara.vifirar.se`) och API-nyckeln.

Nya versioner dyker sedan upp som vanliga HACS-uppdateringar.

## Installation för hand

Går lika bra, men du får uppdatera själv.

1. Ladda ner `vifirar-ha.zip` från sajtens admin under **Inställningar → Home Assistant** (eller
   kopiera `custom_components/vifirar/` från det här repot).
2. Packa upp så att mappen hamnar i `config/custom_components/vifirar/` i din Home Assistant.
3. Starta om Home Assistant och fortsätt från steg 6 ovan.

## Sensorerna

| Sensor | Vad den visar |
| --- | --- |
| Kommer | Antal personer som tackat ja, sällskap inräknat |
| Kommer inte | Antal som tackat nej |
| OSA-svar | Antal svar (hushåll), inte personer |
| Vuxna / Barn | Fördelningen bland dem som kommer |
| Önskelistans poster / bokningar | Hur mycket av listan som är bokad |
| Gästfoton | Antal uppladdade foton |
| Dagar kvar | Nedräkning till eventdatumet |

## Vad som skickas

Endast summor. API:et returnerar aldrig gästernas namn, e-postadresser, allergier, meddelanden
eller foton - bara antal, plus sajtens titel och eventdatum. Det är ett medvetet val: en
API-nyckel som läcker ska inte kunna läcka gästernas uppgifter.

## När nyckeln slutar gälla

Byter eller återkallar du nyckeln på sajten slutar sensorerna uppdateras, och Home Assistant ber
dig logga in igen. Klicka på reparationen, klistra in den nya nyckeln, klart - **entiteterna
behålls**, så automationer och historik överlever ett nyckelbyte.

## Realtidshändelser

Sensorerna pollas var 5:e minut. Vill du ha omedelbara notiser (push när någon OSA:r) kompletterar
du med sajtens **webhooks** (Inställningar → Webhooks) mot en webhook-trigger i Home Assistant -
en färdig guide med exempel-YAML finns i sajtens Home Assistant-sektion.

## Ikonen

Ikonen ligger i `custom_components/vifirar/brand/` (`icon.png` 256x256, `icon@2x.png` 512x512).
Från och med **Home Assistant 2026.3** läser HA brandbilder direkt ur integrationen och låter dem gå
före CDN:en - ingen inställning behövs, och ingen PR till
[home-assistant/brands](https://github.com/home-assistant/brands), vars `custom_integrations`-mapp
numera är märkt legacy.

På äldre Home Assistant hämtas ikonen fortfarande från `brands.home-assistant.io`, som svarar med en
gråruta ("icon not available") för domäner som inte skickats in dit. Uppgradera till 2026.3 eller
senare, så syns den.

Bilderna byggs ur sajtens egna ikoner med `node scripts/ha-brand.mjs` i plattformsrepot.

## Frågor och fel

Skriv till oss via [vifirar.se/kontakt](https://vifirar.se/kontakt?amne=fel) - eller öppna ett
issue här om du hellre gör det.

## Licens

MIT, se [LICENSE](LICENSE).
