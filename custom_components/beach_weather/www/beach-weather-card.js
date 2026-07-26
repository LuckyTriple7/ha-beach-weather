const CARD_TAG = "beach-weather-card";
const EDITOR_TAG = "beach-weather-card-editor";
const DOMAIN = "beach_weather";
const DEFAULT_BACKGROUND = "/beach_weather_static/beach-weather-background.jpg";
const SUNSET_BACKGROUND = "/beach_weather_static/beach-weather-background-sunset.jpg";
const DEFAULT_ASPECT_RATIO = "16:9";
const DEFAULT_TEXT_COLOR = "#ffffff";
const DEFAULT_FONT_SIZE = 16;
const DEFAULT_ICON_SIZE = 28;
const GRID_STEP = 5; // percent — drag positions snap to this grid so values line up easily

const TRANSLATIONS = {
  en: {
    location: "Location",
    preview_hint: "Preview — drag values to position them (snaps to grid, hold Alt for free placement)",
    add_value: "+ Add value",
    advanced: "Advanced",
    background: "Background image",
    bg_default: "Default (sunny)",
    bg_sunset: "Sunset",
    bg_auto: "Automatic (weather)",
    bg_custom: "Custom URL…",
    bg_url: "Image URL",
    aspect_ratio: "Aspect ratio (e.g. 16:9, 4:3, 1:1)",
    text_color: "Text color",
    font_size: "Font size (px)",
    icon_size: "Icon size (px)",
    name: "Name",
    icon: "Icon",
    centered_x: "Centered X",
    centered_y: "Centered Y",
    remove: "Remove",
    no_sensor: "(no sensor)",
    no_items_card: "Beach Weather Card: no values configured.",
    no_state: "–",
  },
  de: {
    location: "Standort",
    preview_hint: "Vorschau — Werte per Drag positionieren (rastet am Raster ein, Alt gedrückt halten für freie Positionierung)",
    add_value: "+ Wert hinzufügen",
    advanced: "Erweitert",
    background: "Hintergrundbild",
    bg_default: "Standard (sonnig)",
    bg_sunset: "Sonnenuntergang",
    bg_auto: "Automatisch (Wetter)",
    bg_custom: "Eigene URL…",
    bg_url: "Bild-URL",
    aspect_ratio: "Seitenverhältnis (z.B. 16:9, 4:3, 1:1)",
    text_color: "Schriftfarbe",
    font_size: "Schriftgröße (px)",
    icon_size: "Icon-Größe (px)",
    name: "Name",
    icon: "Icon",
    centered_x: "X zentriert",
    centered_y: "Y zentriert",
    remove: "Entfernen",
    no_sensor: "(kein Sensor)",
    no_items_card: "Beach Weather Card: keine Werte konfiguriert.",
    no_state: "–",
  },
};

function t(hass, key) {
  const lang = (hass && hass.language ? hass.language : "en").toLowerCase().startsWith("de") ? "de" : "en";
  return TRANSLATIONS[lang][key] || TRANSLATIONS.en[key] || key;
}

// HA weather condition -> bundled background key. Only conditions with a
// dedicated bundled photo need an entry; everything else falls back to the
// default (sunny) photo. Extend this once more bundled photos exist, e.g.
// a real night shot for "clear-night" (currently reuses the sunset photo
// as a placeholder).
const AUTO_BACKGROUND_MAP = {
  "clear-night": "sunset",
};

function findWeatherEntity(hass, deviceId) {
  if (!hass || !deviceId) return null;
  const match = Object.values(hass.entities || {}).find(
    (entity) => entity.device_id === deviceId && entity.entity_id.startsWith("weather.")
  );
  return match ? match.entity_id : null;
}

// "auto" picks a bundled photo from the location's weather.<slug> condition
// (which is also day/night aware, e.g. "clear-night" vs "sunny") — falls
// back to the default (sunny) photo if no weather entity/state is available.
function resolveAutoBackgroundKey(hass, deviceId) {
  const weatherEntityId = findWeatherEntity(hass, deviceId);
  const stateObj = weatherEntityId ? hass.states[weatherEntityId] : null;
  const condition = stateObj ? stateObj.state : null;
  return AUTO_BACKGROUND_MAP[condition] || "";
}

// `background_image` config value: "" -> DEFAULT_BACKGROUND, "sunset" -> SUNSET_BACKGROUND,
// "auto" -> resolved from the location's live weather condition, anything
// else is treated as a literal URL to a user-supplied image.
function resolveBackground(value, hass, deviceId) {
  if (!value) return DEFAULT_BACKGROUND;
  if (value === "auto") return resolveBackground(resolveAutoBackgroundKey(hass, deviceId));
  if (value === "sunset") return SUNSET_BACKGROUND;
  return value;
}

// Sensor-key prefixes (see const.py) used to pre-fill a freshly added card
// with a sensible layout before the user has touched the editor at all.
// `domain` matches by entity domain instead of a "sensor.<key>_" prefix,
// used for the weather.<slug> entity which isn't a "sensor.*".
const STUB_ITEMS = [
  { key: "location", x: 49.63, y: 7.22, show_name: false, show_icon: false, center_x: true },
  { domain: "weather", x: 49.46, y: 21.08, show_name: false, show_icon: true, center_x: true },
  { key: "air_temperature", x: 10, y: 40, show_name: false, show_icon: true },
  { key: "uv_index", x: 10, y: 15, show_name: false, show_icon: true },
  { key: "water_temperature", x: 60, y: 65, show_name: false, show_icon: true },
  { key: "wind_speed", x: 30, y: 40, show_name: false, show_icon: true },
  { key: "wave_height", x: 10, y: 80, show_name: false, show_icon: true },
  { key: "wave_period", x: 30, y: 80, show_name: false, show_icon: true },
  { key: "surf_stars", x: 80, y: 95, show_name: false, show_icon: false },
  { key: "bathing_conditions", x: 83.37, y: 81.51, show_name: false, show_icon: true },
];
const STUB_TEXT_COLOR = "#0a0000";
const STUB_FONT_SIZE = 13;
const STUB_ICON_SIZE = 24;

function devicesForIntegration(hass) {
  if (!hass) return [];
  return Object.values(hass.devices || {}).filter((device) =>
    (device.identifiers || []).some((identifier) => identifier[0] === DOMAIN)
  );
}

function entitiesForDevice(hass, deviceId) {
  if (!hass || !deviceId) return [];
  return Object.values(hass.entities || {})
    // button entities (e.g. "Update Now") have no state worth displaying
    .filter((entity) => entity.device_id === deviceId && !entity.entity_id.startsWith("button."))
    .map((entity) => entity.entity_id)
    .sort();
}

// Maps STUB_ITEMS onto a specific device's actual entity IDs — used both
// for a freshly added card's stub config and when switching the location
// dropdown in the editor, so the default layout re-applies instead of the
// card going empty.
function buildStubItems(hass, deviceId) {
  const entities = entitiesForDevice(hass, deviceId);
  const items = [];
  for (const stub of STUB_ITEMS) {
    const match = entities.find((entityId) =>
      stub.domain ? entityId.startsWith(`${stub.domain}.`) : entityId.startsWith(`sensor.${stub.key}_`)
    );
    if (match) {
      items.push({
        entity: match,
        x: stub.x,
        y: stub.y,
        show_name: stub.show_name ?? true,
        show_icon: stub.show_icon ?? true,
        ...(stub.center_x ? { center_x: true } : {}),
      });
    }
  }
  return items;
}

function entityLabel(hass, entityId) {
  const stateObj = hass?.states?.[entityId];
  return stateObj?.attributes?.friendly_name || entityId;
}

function formatState(hass, stateObj) {
  if (hass?.formatEntityState) {
    try {
      return hass.formatEntityState(stateObj);
    } catch (err) {
      // fall through to manual formatting below
    }
  }
  const unit = stateObj.attributes.unit_of_measurement;
  return unit ? `${stateObj.state} ${unit}` : stateObj.state;
}

class BeachWeatherCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement(EDITOR_TAG);
  }

  static getStubConfig(hass) {
    const device = devicesForIntegration(hass)[0];
    if (!device) {
      return {
        type: `custom:${CARD_TAG}`,
        aspect_ratio: DEFAULT_ASPECT_RATIO,
        text_color: STUB_TEXT_COLOR,
        font_size: STUB_FONT_SIZE,
        icon_size: STUB_ICON_SIZE,
        items: [],
      };
    }
    return {
      type: `custom:${CARD_TAG}`,
      device_id: device.id,
      aspect_ratio: DEFAULT_ASPECT_RATIO,
      background_image: "",
      text_color: STUB_TEXT_COLOR,
      font_size: STUB_FONT_SIZE,
      icon_size: STUB_ICON_SIZE,
      items: buildStubItems(hass, device.id),
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this._config = {
      aspect_ratio: DEFAULT_ASPECT_RATIO,
      background_image: "",
      text_color: DEFAULT_TEXT_COLOR,
      font_size: DEFAULT_FONT_SIZE,
      icon_size: DEFAULT_ICON_SIZE,
      items: [],
      ...config,
    };
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    if (!this._built) {
      this._build();
      this._built = true;
    }
    this._updateValues();
  }

  getCardSize() {
    const [w, h] = (this._config?.aspect_ratio || DEFAULT_ASPECT_RATIO).split(":").map(Number);
    if (!w || !h) return 3;
    return Math.max(1, Math.round((h / w) * 4));
  }

  _build() {
    this.innerHTML = "";
    const card = document.createElement("ha-card");
    card.style.overflow = "hidden";

    if (!this._config.items || this._config.items.length === 0) {
      const notice = document.createElement("div");
      notice.style.padding = "16px";
      notice.textContent = t(this._hass, "no_items_card");
      card.appendChild(notice);
      this.appendChild(card);
      this._itemNodes = [];
      return;
    }

    const container = document.createElement("div");
    container.style.position = "relative";
    container.style.width = "100%";
    container.style.aspectRatio = (this._config.aspect_ratio || DEFAULT_ASPECT_RATIO).replace(":", "/");
    container.style.backgroundSize = "cover";
    container.style.backgroundPosition = "center";
    this._container = container;
    this._applyBackground();

    this._itemNodes = (this._config.items || []).map((item) => {
      const node = this._buildItemNode(item);
      container.appendChild(node.el);
      return node;
    });

    card.appendChild(container);
    this.appendChild(card);
  }

  _applyBackground() {
    if (!this._container) return;
    const url = resolveBackground(this._config.background_image, this._hass, this._config.device_id);
    this._container.style.backgroundImage = `url("${url}")`;
  }

  _buildItemNode(item) {
    const el = document.createElement("div");
    el.style.position = "absolute";
    el.style.left = item.center_x ? "50%" : `${item.x ?? 50}%`;
    el.style.top = item.center_y ? "50%" : `${item.y ?? 50}%`;
    el.style.transform = "translate(-50%, -50%)";
    el.style.display = "flex";
    el.style.flexDirection = "column";
    el.style.alignItems = "center";
    el.style.gap = "2px";
    el.style.textShadow = "0 1px 3px rgba(0,0,0,0.6)";
    el.style.color = this._config.text_color || DEFAULT_TEXT_COLOR;
    el.style.textAlign = "center";
    el.style.whiteSpace = "nowrap";
    el.style.cursor = "pointer";

    if (item.entity) {
      el.addEventListener("click", () => {
        this.dispatchEvent(
          new CustomEvent("hass-more-info", {
            detail: { entityId: item.entity },
            bubbles: true,
            composed: true,
          })
        );
      });
    }

    const fontSize = this._config.font_size || DEFAULT_FONT_SIZE;
    const iconSize = this._config.icon_size || DEFAULT_ICON_SIZE;

    let icon = null;
    if (item.show_icon !== false) {
      icon = document.createElement("ha-state-icon");
      icon.style.setProperty("--mdc-icon-size", `${iconSize}px`);
      el.appendChild(icon);
    }

    const value = document.createElement("span");
    value.style.fontSize = `${fontSize}px`;
    value.style.fontWeight = "600";
    el.appendChild(value);

    let name = null;
    if (item.show_name) {
      name = document.createElement("span");
      name.style.fontSize = `${Math.round(fontSize * 0.7)}px`;
      name.style.opacity = "0.9";
      el.appendChild(name);
    }

    return { el, icon, value, name, item };
  }

  _updateValues() {
    if (!this._hass || !this._itemNodes) return;
    if (this._config.background_image === "auto") this._applyBackground();
    for (const node of this._itemNodes) {
      const stateObj = this._hass.states[node.item.entity];
      if (!stateObj) {
        node.value.textContent = t(this._hass, "no_state");
        continue;
      }
      if (node.icon) {
        node.icon.hass = this._hass;
        node.icon.stateObj = stateObj;
      }
      node.value.textContent = formatState(this._hass, stateObj);
      node.el.title = stateObj.attributes.friendly_name || node.item.entity;
      if (node.name) {
        node.name.textContent = stateObj.attributes.friendly_name || node.item.entity;
      }
    }
  }
}

class BeachWeatherCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = {
      aspect_ratio: DEFAULT_ASPECT_RATIO,
      background_image: "",
      text_color: DEFAULT_TEXT_COLOR,
      font_size: DEFAULT_FONT_SIZE,
      icon_size: DEFAULT_ICON_SIZE,
      items: [],
      ...config,
    };
    if (this._hass) this._buildOnce();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._config && !this._built) this._buildOnce();
  }

  _fireChanged() {
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }

  _buildOnce() {
    this.innerHTML = `
      <style>
        .bwc-editor { display: flex; flex-direction: column; gap: 16px; padding: 8px 0; }
        .bwc-row { display: flex; flex-direction: column; gap: 4px; }
        .bwc-row label { font-size: 0.85em; opacity: 0.8; }
        .bwc-canvas { position: relative; width: 100%; background-size: cover; background-position: center;
          border: 1px solid var(--divider-color); border-radius: 8px; overflow: hidden; user-select: none; }
        .bwc-item { position: absolute; transform: translate(-50%, -50%); display: flex; flex-direction: column;
          align-items: center; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.6); cursor: grab;
          touch-action: none; padding: 2px 4px; white-space: nowrap; }
        .bwc-item.dragging { cursor: grabbing; outline: 2px dashed #fff; }
        .bwc-item span { font-size: 0.8em; font-weight: 600; }
        .bwc-list { display: flex; flex-direction: column; gap: 8px; }
        .bwc-item-row { display: grid; grid-template-columns: 1fr auto auto auto auto auto; gap: 8px; align-items: center; }
        .bwc-add { align-self: flex-start; }
        .bwc-advanced { display: flex; flex-direction: column; gap: 8px; }
        input[type="text"], select { padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color);
          background: var(--card-background-color, #fff); color: var(--primary-text-color); }
        .bwc-toggle { display: flex; align-items: center; gap: 4px; font-size: 0.85em; white-space: nowrap; }
        button { cursor: pointer; }
      </style>
      <div class="bwc-editor">
        <div class="bwc-row">
          <label>${t(this._hass, "location")}</label>
          <select id="device"></select>
        </div>
        <div class="bwc-row">
          <label>${t(this._hass, "preview_hint")}</label>
          <div class="bwc-canvas" id="canvas"></div>
        </div>
        <div class="bwc-list" id="list"></div>
        <button class="bwc-add" id="add">${t(this._hass, "add_value")}</button>
        <details class="bwc-advanced">
          <summary>${t(this._hass, "advanced")}</summary>
          <div class="bwc-row">
            <label>${t(this._hass, "background")}</label>
            <select id="bg-preset">
              <option value="">${t(this._hass, "bg_default")}</option>
              <option value="sunset">${t(this._hass, "bg_sunset")}</option>
              <option value="auto">${t(this._hass, "bg_auto")}</option>
              <option value="custom">${t(this._hass, "bg_custom")}</option>
            </select>
          </div>
          <div class="bwc-row" id="bg-custom-row">
            <label>${t(this._hass, "bg_url")}</label>
            <input type="text" id="bg-custom" />
          </div>
          <div class="bwc-row">
            <label>${t(this._hass, "aspect_ratio")}</label>
            <input type="text" id="aspect" />
          </div>
          <div class="bwc-row">
            <label>${t(this._hass, "text_color")}</label>
            <input type="color" id="text-color" />
          </div>
          <div class="bwc-row">
            <label>${t(this._hass, "font_size")}</label>
            <input type="number" id="font-size" min="8" max="72" />
          </div>
          <div class="bwc-row">
            <label>${t(this._hass, "icon_size")}</label>
            <input type="number" id="icon-size" min="8" max="96" />
          </div>
        </details>
      </div>
    `;
    this._built = true;

    this.querySelector("#device").addEventListener("change", (ev) => {
      const deviceId = ev.target.value;
      const items = deviceId ? buildStubItems(this._hass, deviceId) : [];
      this._config = { ...this._config, device_id: deviceId, items };
      this._fireChanged();
      this._renderDynamic();
    });
    this.querySelector("#add").addEventListener("click", () => this._addItem());
    this.querySelector("#bg-preset").addEventListener("change", (ev) => {
      const preset = ev.target.value;
      const background_image = preset === "custom" ? "" : preset;
      this._config = { ...this._config, background_image };
      this._fireChanged();
      this._renderDynamic();
    });
    this.querySelector("#bg-custom").addEventListener("change", (ev) => {
      this._config = { ...this._config, background_image: ev.target.value };
      this._fireChanged();
      this._renderDynamic();
    });
    this.querySelector("#aspect").addEventListener("change", (ev) => {
      this._config = { ...this._config, aspect_ratio: ev.target.value || DEFAULT_ASPECT_RATIO };
      this._fireChanged();
      this._renderDynamic();
    });
    this.querySelector("#text-color").addEventListener("change", (ev) => {
      this._config = { ...this._config, text_color: ev.target.value || DEFAULT_TEXT_COLOR };
      this._fireChanged();
      this._renderDynamic();
    });
    this.querySelector("#font-size").addEventListener("change", (ev) => {
      this._config = { ...this._config, font_size: Number(ev.target.value) || DEFAULT_FONT_SIZE };
      this._fireChanged();
      this._renderDynamic();
    });
    this.querySelector("#icon-size").addEventListener("change", (ev) => {
      this._config = { ...this._config, icon_size: Number(ev.target.value) || DEFAULT_ICON_SIZE };
      this._fireChanged();
      this._renderDynamic();
    });

    this._renderDynamic();
  }

  _renderDynamic() {
    const deviceSelect = this.querySelector("#device");
    const devices = devicesForIntegration(this._hass).sort((a, b) =>
      (a.name_by_user || a.name || "").localeCompare(b.name_by_user || b.name || "")
    );
    deviceSelect.innerHTML =
      `<option value="">–</option>` +
      devices
        .map(
          (device) =>
            `<option value="${device.id}">${device.name_by_user || device.name || device.id}</option>`
        )
        .join("");
    deviceSelect.value = this._config.device_id || "";

    const bg = this._config.background_image || "";
    const isPreset = bg === "" || bg === "sunset" || bg === "auto";
    this.querySelector("#bg-preset").value = isPreset ? bg : "custom";
    this.querySelector("#bg-custom-row").style.display = isPreset ? "none" : "";
    this.querySelector("#bg-custom").value = isPreset ? "" : bg;
    this.querySelector("#aspect").value = this._config.aspect_ratio || DEFAULT_ASPECT_RATIO;
    this.querySelector("#text-color").value = this._config.text_color || DEFAULT_TEXT_COLOR;
    this.querySelector("#font-size").value = this._config.font_size || DEFAULT_FONT_SIZE;
    this.querySelector("#icon-size").value = this._config.icon_size || DEFAULT_ICON_SIZE;

    this._renderCanvas();
    this._renderList();
  }

  _renderCanvas() {
    const canvas = this.querySelector("#canvas");
    canvas.innerHTML = "";
    canvas.style.aspectRatio = (this._config.aspect_ratio || DEFAULT_ASPECT_RATIO).replace(":", "/");
    canvas.style.backgroundImage = `url("${resolveBackground(
      this._config.background_image,
      this._hass,
      this._config.device_id
    )}")`;

    const grid = document.createElement("div");
    grid.style.position = "absolute";
    grid.style.inset = "0";
    grid.style.pointerEvents = "none";
    grid.style.backgroundImage =
      `repeating-linear-gradient(to right, rgba(255,255,255,0.35) 0 1px, transparent 1px ${GRID_STEP}%),` +
      `repeating-linear-gradient(to bottom, rgba(255,255,255,0.35) 0 1px, transparent 1px ${GRID_STEP}%)`;
    canvas.appendChild(grid);

    (this._config.items || []).forEach((item, index) => {
      const el = document.createElement("div");
      el.className = "bwc-item";
      el.style.left = item.center_x ? "50%" : `${item.x ?? 50}%`;
      el.style.top = item.center_y ? "50%" : `${item.y ?? 50}%`;
      el.style.color = this._config.text_color || DEFAULT_TEXT_COLOR;

      if (item.show_icon !== false && item.entity) {
        const stateObj = this._hass.states[item.entity];
        if (stateObj) {
          const icon = document.createElement("ha-state-icon");
          icon.style.setProperty("--mdc-icon-size", `${this._config.icon_size || DEFAULT_ICON_SIZE}px`);
          icon.hass = this._hass;
          icon.stateObj = stateObj;
          el.appendChild(icon);
        }
      }

      const value = document.createElement("span");
      value.style.fontSize = `${this._config.font_size || DEFAULT_FONT_SIZE}px`;
      value.textContent = item.entity ? entityLabel(this._hass, item.entity) : t(this._hass, "no_sensor");
      el.appendChild(value);

      el.addEventListener("pointerdown", (ev) => this._startDrag(ev, index, el, canvas));
      canvas.appendChild(el);
    });
  }

  _startDrag(ev, index, el, canvas) {
    ev.preventDefault();
    el.classList.add("dragging");
    el.setPointerCapture(ev.pointerId);

    const centerX = !!this._config.items[index].center_x;
    const centerY = !!this._config.items[index].center_y;

    const move = (moveEv) => {
      const rect = canvas.getBoundingClientRect();
      let x = ((moveEv.clientX - rect.left) / rect.width) * 100;
      let y = ((moveEv.clientY - rect.top) / rect.height) * 100;
      x = Math.min(100, Math.max(0, x));
      y = Math.min(100, Math.max(0, y));
      // Snap to the grid drawn on the canvas — makes lining values up on
      // the same row/column a drag instead of a pixel-hunting exercise.
      if (!moveEv.altKey) {
        x = Math.round(x / GRID_STEP) * GRID_STEP;
        y = Math.round(y / GRID_STEP) * GRID_STEP;
      }
      if (centerX) x = 50; // horizontally centered items only move vertically
      if (centerY) y = 50; // vertically centered items only move horizontally
      el.style.left = `${x}%`;
      el.style.top = `${y}%`;
      this._config.items[index] = { ...this._config.items[index], x, y };
    };

    const up = () => {
      el.classList.remove("dragging");
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      this._config = { ...this._config, items: [...this._config.items] };
      this._fireChanged();
    };

    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
  }

  _renderList() {
    const list = this.querySelector("#list");
    list.innerHTML = "";
    const entities = entitiesForDevice(this._hass, this._config.device_id);

    (this._config.items || []).forEach((item, index) => {
      const row = document.createElement("div");
      row.className = "bwc-item-row";

      const select = document.createElement("select");
      select.innerHTML = entities
        .map(
          (entityId) =>
            `<option value="${entityId}" ${entityId === item.entity ? "selected" : ""}>${entityLabel(
              this._hass,
              entityId
            )}</option>`
        )
        .join("");
      select.addEventListener("change", (ev) => this._updateItem(index, { entity: ev.target.value }));
      row.appendChild(select);

      row.appendChild(
        this._toggle(t(this._hass, "name"), item.show_name === true, (checked) =>
          this._updateItem(index, { show_name: checked })
        )
      );
      row.appendChild(
        this._toggle(t(this._hass, "icon"), item.show_icon !== false, (checked) =>
          this._updateItem(index, { show_icon: checked })
        )
      );
      row.appendChild(
        this._toggle(t(this._hass, "centered_x"), item.center_x === true, (checked) =>
          this._updateItem(index, { center_x: checked })
        )
      );
      row.appendChild(
        this._toggle(t(this._hass, "centered_y"), item.center_y === true, (checked) =>
          this._updateItem(index, { center_y: checked })
        )
      );

      const remove = document.createElement("button");
      remove.textContent = "×";
      remove.title = t(this._hass, "remove");
      remove.addEventListener("click", () => this._removeItem(index));
      row.appendChild(remove);

      list.appendChild(row);
    });
  }

  _toggle(label, checked, onChange) {
    const wrap = document.createElement("label");
    wrap.className = "bwc-toggle";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = checked;
    input.addEventListener("change", (ev) => onChange(ev.target.checked));
    wrap.appendChild(input);
    wrap.appendChild(document.createTextNode(label));
    return wrap;
  }

  _updateItem(index, patch) {
    const items = [...this._config.items];
    items[index] = { ...items[index], ...patch };
    this._config = { ...this._config, items };
    this._fireChanged();
    this._renderDynamic();
  }

  _removeItem(index) {
    const items = [...this._config.items];
    items.splice(index, 1);
    this._config = { ...this._config, items };
    this._fireChanged();
    this._renderDynamic();
  }

  _addItem() {
    const entities = entitiesForDevice(this._hass, this._config.device_id);
    const used = new Set((this._config.items || []).map((i) => i.entity));
    const next = entities.find((entityId) => !used.has(entityId)) || entities[0] || "";
    const items = [
      ...(this._config.items || []),
      { entity: next, x: 50, y: 50, show_name: true, show_icon: true },
    ];
    this._config = { ...this._config, items };
    this._fireChanged();
    this._renderDynamic();
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, BeachWeatherCard);
}
if (!customElements.get(EDITOR_TAG)) {
  customElements.define(EDITOR_TAG, BeachWeatherCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Beach Weather Card",
    description: "Beach/water values freely positioned over a background photo.",
    preview: true,
  });
}
