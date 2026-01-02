# 🏠 Guía Completa: Integración Gree/Daitsu AC en Home Assistant

## 📋 Índice
1. [Requisitos Previos](#requisitos)
2. [Instalación Rápida](#instalación-rápida)
3. [Instalación Completa](#instalación-completa)
4. [Configuración](#configuración)
5. [Automaciones Ejemplo](#automaciones)
6. [Lovelace Cards](#lovelace)
7. [Troubleshooting](#troubleshooting)

---

## <a name="requisitos"></a>📦 Requisitos Previos

- Home Assistant instalado (2023.12+)
- Broadlink RM3/RM4/Mini con IP fija configurada
- IP addresses de cada Broadlink conocidas
- Acceso SSH o File Editor en Home Assistant

**Dependencias que se instalan automáticamente:**
- `python-broadlink >= 0.18.0`
- `pyyaml` (ya incluido en HA)

---

## <a name="instalación-rápida"></a>⚡ Instalación Rápida (YAML Simple)

Si solo tienes 1-2 ACs, esta es la forma más fácil.

### Paso 1: Editar `configuration.yaml`

```yaml
climate:
  - platform: broadlink
    name: "Dormitorio AC"
    host: 192.168.1.100
    mac: "34:EA:34:XX:XX:XX"  # MAC del Broadlink
```

Obtén el MAC del Broadlink:
1. Abre app Broadlink en móvil
2. Settings → Device info → MAC address

### Paso 2: Guardar y Reiniciar

```
Settings → System → Restart
```

### Paso 3: Verificar

En **Settings → Devices & Services → Entities**, busca `climate.dormitorio_ac`

---

## <a name="instalación-completa"></a>📦 Instalación Completa (Custom Component)

Para control total, múltiples ACs, automaciones avanzadas.

### Paso 1: Crear Estructura de Directorios

Usa **File Editor** en Home Assistant:

```
/config/custom_components/gree_ac/
├── __init__.py
├── manifest.json
├── climate.py
├── const.py
├── config_flow.py
├── strings.json
└── translations/
    └── es.json
```

### Paso 2: Crear `manifest.json`

**File:** `/config/custom_components/gree_ac/manifest.json`

```json
{
  "manifest_version": 1,
  "domain": "gree_ac",
  "name": "Gree/Daitsu Air Conditioner",
  "codeowners": ["@tu_usuario"],
  "config_flow": true,
  "documentation": "https://github.com/tu_usuario/gree-ac",
  "requirements": ["broadlink>=0.18.0"],
  "version": "1.0.0",
  "iot_class": "local_polling",
  "platforms": ["climate"]
}
```

### Paso 3: Crear `__init__.py`

**File:** `/config/custom_components/gree_ac/__init__.py`

```python
"""Gree/Daitsu AC Integration"""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "gree_ac"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Gree AC integration"""
    return True


async def async_setup_entry(hass, entry):
    """Set up from config entry"""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True
```

### Paso 4: Crear `const.py`

**File:** `/config/custom_components/gree_ac/const.py`

```python
"""Constants for Gree AC Integration"""

DOMAIN = "gree_ac"

# Temperature ranges
MIN_TEMP = 16
MAX_TEMP = 30
TEMP_STEP = 1

# HVAC modes
HVAC_MODES = ["off", "heat", "cool", "dry", "fan_only", "auto"]
FAN_MODES = ["auto", "max", "med", "min"]
SWING_MODES = ["off", "vertical", "horizontal", "both"]

# Gree protocol mapping
GREE_MODES = {
    "heat": 0x00,
    "cool": 0x02,
    "dry": 0x03,
    "fan_only": 0x04,
    "auto": 0x05,
}

GREE_FAN_MODES = {
    "auto": 0b00,
    "max": 0b01,
    "med": 0b10,
    "min": 0b11,
}
```

### Paso 5: Crear `climate.py`

Usa el archivo `gree_ac_climate.py` que ya creamos. Cópialo a:

**File:** `/config/custom_components/gree_ac/climate.py`

### Paso 6: Crear `config_flow.py`

**File:** `/config/custom_components/gree_ac/config_flow.py`

```python
"""Config flow for Gree AC"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from .const import DOMAIN


class GreeACConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user step"""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_NAME): str,
                }
            ),
        )
```

### Paso 7: Crear `strings.json`

**File:** `/config/custom_components/gree_ac/strings.json`

```json
{
  "config": {
    "step": {
      "user": {
        "description": "Set up your Gree AC",
        "data": {
          "host": "IP Address of Broadlink",
          "name": "Name of the AC"
        }
      }
    }
  }
}
```

### Paso 8: Crear traducción al español

**File:** `/config/custom_components/gree_ac/translations/es.json`

```json
{
  "config": {
    "step": {
      "user": {
        "description": "Configura tu Aire Acondicionado Gree",
        "data": {
          "host": "Dirección IP del Broadlink",
          "name": "Nombre del Aire Acondicionado"
        }
      }
    }
  }
}
```

### Paso 9: Reiniciar Home Assistant

```
Settings → System → Restart
```

---

## <a name="configuración"></a>⚙️ Configuración en Home Assistant

### Opción A: UI (Recomendado)

1. **Settings → Devices & Services → Integrations**
2. **Create Integration** → Buscar "Gree AC"
3. Rellenar:
   - **IP Address:** `192.168.1.100`
   - **Name:** `Dormitorio AC`
4. **Create**

Repite para cada Broadlink que tengas.

### Opción B: YAML

En `configuration.yaml`:

```yaml
climate:
  - platform: gree_ac
    host: 192.168.1.100
    name: "Dormitorio AC"

  - platform: gree_ac
    host: 192.168.1.101
    name: "Salón AC"

  - platform: gree_ac
    host: 192.168.1.102
    name: "Cocina AC"
```

Luego reiniciar Home Assistant.

---

## <a name="automaciones"></a>🤖 Automaciones Ejemplo

### 1. Encender AC a temperatura específica por horario

```yaml
automation:
  - alias: "AC Dormitorio - Noche a 24°C"
    triggers:
      - trigger: time
        at: "22:00:00"
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.dormitorio_ac
        data:
          temperature: 24
          hvac_mode: cool
      - action: climate.set_fan_mode
        target:
          entity_id: climate.dormitorio_ac
        data:
          fan_mode: auto
```

### 2. Apagar AC a hora fija

```yaml
  - alias: "AC Dormitorio - Apagar"
    triggers:
      - trigger: time
        at: "08:00:00"
    actions:
      - action: climate.turn_off
        target:
          entity_id: climate.dormitorio_ac
```

### 3. AC automático según temperatura exterior

```yaml
  - alias: "AC Salón - Automático por temperatura"
    triggers:
      - trigger: numeric_state
        entity_id: weather.casa
        attribute: temperature
        above: 28
    actions:
      - action: climate.set_hvac_mode
        target:
          entity_id: climate.salon_ac
        data:
          hvac_mode: cool
      - action: climate.set_temperature
        target:
          entity_id: climate.salon_ac
        data:
          temperature: 26
```

### 4. Cambiar temperatura mediante input_number

```yaml
automation:
  - alias: "AC Dormitorio - Temp desde slider"
    triggers:
      - trigger: state
        entity_id: input_number.dormitorio_temp
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.dormitorio_ac
        data:
          temperature: "{{ states('input_number.dormitorio_temp') | int }}"
```

Helper a añadir en `configuration.yaml`:

```yaml
input_number:
  dormitorio_temp:
    name: "Temperatura Dormitorio"
    min: 16
    max: 30
    step: 1
    unit_of_measurement: "°C"
```

---

## <a name="lovelace"></a>🎨 Tarjetas Lovelace

### Tarjeta Thermostat Simple

```yaml
type: thermostat
entity: climate.dormitorio_ac
```

### Tarjeta Climate Entities (Recomendado)

```yaml
type: custom:climate-entities-card
entity: climate.dormitorio_ac
hide:
  - target_temperature_step
  - current_humidity
  - fan_only_icon
  - swing_change
icons:
  default: []
```

(Requiere instalar `climate-entities-card` vía HACS)

### Dashboard Multi-AC

```yaml
type: grid
cards:
  - type: thermostat
    entity: climate.dormitorio_ac
    
  - type: thermostat
    entity: climate.salon_ac
    
  - type: thermostat
    entity: climate.cocina_ac
```

### Panel de Control Avanzado

```yaml
type: vertical-stack
cards:
  - type: heading
    heading: "Control de Aire Acondicionado"
  
  - type: grid
    columns: 3
    cards:
      - type: thermostat
        entity: climate.dormitorio_ac
      
      - type: thermostat
        entity: climate.salon_ac
      
      - type: thermostat
        entity: climate.cocina_ac
  
  - type: entities
    entities:
      - input_number.dormitorio_temp
      - climate.dormitorio_ac
    title: "Dormitorio Detalles"
```

---

## <a name="troubleshooting"></a>🔧 Solución de Problemas

### Problema: "Integración no aparece"

**Solución:**
1. Verifica que los archivos están en `/config/custom_components/gree_ac/`
2. Reinicia Home Assistant (no solo reload)
3. Revisa logs: **Settings → System & Maintenance → Logs**

### Problema: "Error connecting to Broadlink"

**Solución:**
1. Verifica IP del Broadlink: `ping 192.168.1.100`
2. Asegúrate de que IP es **FIJA** (no dinámica)
3. Comprueba que Broadlink está encendido (luz LED)
4. Intenta reconectar en app Broadlink primero

### Problema: "AC no responde"

**Solución:**
1. Prueba el mando físico primero (verifica que funciona)
2. Abre logs de HA en DEBUG:
   ```yaml
   logger:
     logs:
       custom_components.gree_ac: debug
   ```
3. Envia comando manual:
   ```yaml
   action: remote.send_command
   target:
     entity_id: remote.broadlink
   data:
     command: "b64:JgCSAAA..."
   ```

### Problema: "Temperatura no actualiza"

**Por diseño:** El AC infrarrojo no puede confirmar temperatura (no hay feedback)

**Solución:** Añade un sensor de temperatura independiente:

```yaml
climate:
  - platform: gree_ac
    host: 192.168.1.100
    name: "Dormitorio AC"
    current_temperature_entity: sensor.dormitorio_temp  # Sensor independiente
```

### Problema: "Múltiples ACs no sincronizados"

**Por diseño:** Cada AC es independiente

**Solución:** Crea una automation que sincronice todos:

```yaml
automation:
  - alias: "Sincronizar todos los ACs"
    triggers:
      - trigger: state
        entity_id: climate.dormitorio_ac
        attribute: target_temperature
    actions:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.salon_ac
            - climate.cocina_ac
        data:
          temperature: "{{ state_attr('climate.dormitorio_ac', 'temperature') }}"
```

---

## 📞 Support & Debugging

### Activar DEBUG Logging

```yaml
logger:
  logs:
    custom_components.gree_ac: debug
    broadlink: debug
```

Luego revisar en **Logs** de HA.

### Verificar Estado AC

```
Developer Tools → States → climate.dormitorio_ac
```

Verás JSON con estado actual.

### Test Manual de Temperatura

```yaml
service: climate.set_temperature
target:
  entity_id: climate.dormitorio_ac
data:
  temperature: 25
  hvac_mode: cool
```

---

## ✅ Checklist de Instalación

- [ ] Broadlink RM conectado a WiFi con IP fija
- [ ] Home Assistant actualizado (2023.12+)
- [ ] Archivos creados en `/config/custom_components/gree_ac/`
- [ ] Home Assistant reiniciado después de copiar archivos
- [ ] Integración añadida (UI o YAML)
- [ ] Climate entity aparece en Devices & Services
- [ ] Prueba: Cambiar temperatura desde HA
- [ ] Verificar en logs si hay errores
- [ ] Configurar automaciones deseadas
- [ ] Añadir tarjetas a Lovelace

---

## 🚀 Próximos Pasos

- **HACS:** Publique la integración en HACS para instalación automática
- **Config Flow UI:** Mejore el flujo de configuración
- **State Feedback:** Integre sensor de estado del AC
- **History Stats:** Registre consumo histórico
- **Automations Templates:** Cree templates reutilizables

---

**¿Problemas?** Revisa los logs y comparte en los comentarios.

**¿Funciona?** ¡Comparte tu configuración con la comunidad!
