const CARD_TAG = "beach-weather-card";
const EDITOR_TAG = "beach-weather-card-editor";
const DOMAIN = "beach_weather";
const DEFAULT_BACKGROUND = "/beach_weather_static/beach-weather-background.jpg";
const SUNSET_BACKGROUND = "/beach_weather_static/beach-weather-background-sunset.jpg";
const DEFAULT_ASPECT_RATIO = "16:9";
const DEFAULT_TEXT_COLOR = "#ffffff";

// `background_image` config value: "" -> DEFAULT_BACKGROUND, "sunset" -> SUNSET_BACKGROUND,
// anything else is treated as a literal URL to a user-supplied image.
function resolveBackground(value) {
  if (!value) return DEFAULT_BACKGROUND;
  if (value === "sunset") return SUNSET_BACKGROUND;
  return value;
}

// Sensor-key prefixes (see const.py) used to pre-fill a freshly added card
// with a sensible layout before the user has touched the editor at all.
const STUB_ITEMS = [
  { key: "water_temperature", x: 15, y: 20 },
  { key: "wave_height", x: 15, y: 38 },
  { key: "wind_speed", x: 15, y: 56 },
  { key: "bathing_conditions", x: 15, y: 74 },
];

function devicesForIntegration(hass) {
  if (!hass) return [];
  return Object.values(hass.devices || {}).filter((device) =>
    (device.identifiers || []).some((identifier) => identifier[0] === DOMAIN)
  );
}

function entitiesForDevice(hass, deviceId) {
  if (!hass || !deviceId) return [];
  return Object.values(hass.entities || {})
    .filter((entity) => entity.device_id === deviceId)
    .map((entity) => entity.entity_id)
    .sort();
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
      return { type: `custom:${CARD_TAG}`, aspect_ratio: DEFAULT_ASPECT_RATIO, items: [] };
    }
    const entities = entitiesForDevice(hass, device.id);
    const items = [];
    for (const stub of STUB_ITEMS) {
      const match = entities.find((entityId) => entityId.startsWith(`sensor.${stub.key}_`));
      if (match) {
        items.push({ entity: match, x: stub.x, y: stub.y, show_name: true, show_icon: true });
      }
    }
    return {
      type: `custom:${CARD_TAG}`,
      device_id: device.id,
      aspect_ratio: DEFAULT_ASPECT_RATIO,
      background_image: "",
      items,
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
      notice.textContent = "Beach Weather Card: keine Werte konfiguriert.";
      card.appendChild(notice);
      this.appendChild(card);
      this._itemNodes = [];
      return;
    }

    const container = document.createElement("div");
    container.style.position = "relative";
    container.style.width = "100%";
    container.style.aspectRatio = (this._config.aspect_ratio || DEFAULT_ASPECT_RATIO).replace(":", "/");
    container.style.backgroundImage = `url("${resolveBackground(this._config.background_image)}")`;
    container.style.backgroundSize = "cover";
    container.style.backgroundPosition = "center";

    this._itemNodes = (this._config.items || []).map((item) => {
      const node = this._buildItemNode(item);
      container.appendChild(node.el);
      return node;
    });

    card.appendChild(container);
    this.appendChild(card);
  }

  _buildItemNode(item) {
    const el = document.createElement("div");
    el.style.position = "absolute";
    el.style.left = `${item.x ?? 50}%`;
    el.style.top = `${item.y ?? 50}%`;
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

    let icon = null;
    if (item.show_icon !== false) {
      icon = document.createElement("ha-state-icon");
      icon.style.setProperty("--mdc-icon-size", "28px");
      el.appendChild(icon);
    }

    const value = document.createElement("span");
    value.style.fontSize = "1.1em";
    value.style.fontWeight = "600";
    el.appendChild(value);

    let name = null;
    if (item.show_name) {
      name = document.createElement("span");
      name.style.fontSize = "0.75em";
      name.style.opacity = "0.9";
      el.appendChild(name);
    }

    return { el, icon, value, name, item };
  }

  _updateValues() {
    if (!this._hass || !this._itemNodes) return;
    for (const node of this._itemNodes) {
      const stateObj = this._hass.states[node.item.entity];
      if (!stateObj) {
        node.value.textContent = "–";
        continue;
      }
      if (node.icon) {
        node.icon.hass = this._hass;
        node.icon.stateObj = stateObj;
      }
      node.value.textContent = formatState(this._hass, stateObj);
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
        .bwc-item-row { display: grid; grid-template-columns: 1fr auto auto auto; gap: 8px; align-items: center; }
        .bwc-add { align-self: flex-start; }
        .bwc-advanced { display: flex; flex-direction: column; gap: 8px; }
        input[type="text"], select { padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color);
          background: var(--card-background-color, #fff); color: var(--primary-text-color); }
        .bwc-toggle { display: flex; align-items: center; gap: 4px; font-size: 0.85em; white-space: nowrap; }
        button { cursor: pointer; }
      </style>
      <div class="bwc-editor">
        <div class="bwc-row">
          <label>Standort</label>
          <select id="device"></select>
        </div>
        <div class="bwc-row">
          <label>Vorschau — Werte per Drag positionieren</label>
          <div class="bwc-canvas" id="canvas"></div>
        </div>
        <div class="bwc-list" id="list"></div>
        <button class="bwc-add" id="add">+ Wert hinzufügen</button>
        <details class="bwc-advanced">
          <summary>Erweitert</summary>
          <div class="bwc-row">
            <label>Hintergrundbild</label>
            <select id="bg-preset">
              <option value="">Standard (sonnig)</option>
              <option value="sunset">Sonnenuntergang</option>
              <option value="custom">Eigene URL…</option>
            </select>
          </div>
          <div class="bwc-row" id="bg-custom-row">
            <label>Bild-URL</label>
            <input type="text" id="bg-custom" />
          </div>
          <div class="bwc-row">
            <label>Seitenverhältnis (z.B. 16:9, 4:3, 1:1)</label>
            <input type="text" id="aspect" />
          </div>
          <div class="bwc-row">
            <label>Schriftfarbe</label>
            <input type="color" id="text-color" />
          </div>
        </details>
      </div>
    `;
    this._built = true;

    this.querySelector("#device").addEventListener("change", (ev) => {
      this._config = { ...this._config, device_id: ev.target.value, items: [] };
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
    const isPreset = bg === "" || bg === "sunset";
    this.querySelector("#bg-preset").value = isPreset ? bg : "custom";
    this.querySelector("#bg-custom-row").style.display = isPreset ? "none" : "";
    this.querySelector("#bg-custom").value = isPreset ? "" : bg;
    this.querySelector("#aspect").value = this._config.aspect_ratio || DEFAULT_ASPECT_RATIO;
    this.querySelector("#text-color").value = this._config.text_color || DEFAULT_TEXT_COLOR;

    this._renderCanvas();
    this._renderList();
  }

  _renderCanvas() {
    const canvas = this.querySelector("#canvas");
    canvas.innerHTML = "";
    canvas.style.aspectRatio = (this._config.aspect_ratio || DEFAULT_ASPECT_RATIO).replace(":", "/");
    canvas.style.backgroundImage = `url("${resolveBackground(this._config.background_image)}")`;

    (this._config.items || []).forEach((item, index) => {
      const el = document.createElement("div");
      el.className = "bwc-item";
      el.style.left = `${item.x ?? 50}%`;
      el.style.top = `${item.y ?? 50}%`;
      el.style.color = this._config.text_color || DEFAULT_TEXT_COLOR;

      if (item.show_icon !== false && item.entity) {
        const stateObj = this._hass.states[item.entity];
        if (stateObj) {
          const icon = document.createElement("ha-state-icon");
          icon.style.setProperty("--mdc-icon-size", "22px");
          icon.hass = this._hass;
          icon.stateObj = stateObj;
          el.appendChild(icon);
        }
      }

      const value = document.createElement("span");
      value.textContent = item.entity ? entityLabel(this._hass, item.entity) : "(kein Sensor)";
      el.appendChild(value);

      el.addEventListener("pointerdown", (ev) => this._startDrag(ev, index, el, canvas));
      canvas.appendChild(el);
    });
  }

  _startDrag(ev, index, el, canvas) {
    ev.preventDefault();
    el.classList.add("dragging");
    el.setPointerCapture(ev.pointerId);

    const move = (moveEv) => {
      const rect = canvas.getBoundingClientRect();
      let x = ((moveEv.clientX - rect.left) / rect.width) * 100;
      let y = ((moveEv.clientY - rect.top) / rect.height) * 100;
      x = Math.min(100, Math.max(0, x));
      y = Math.min(100, Math.max(0, y));
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
        this._toggle("Name", item.show_name === true, (checked) =>
          this._updateItem(index, { show_name: checked })
        )
      );
      row.appendChild(
        this._toggle("Icon", item.show_icon !== false, (checked) =>
          this._updateItem(index, { show_icon: checked })
        )
      );

      const remove = document.createElement("button");
      remove.textContent = "×";
      remove.title = "Entfernen";
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
    description: "Strand-/Wetterwerte frei positioniert über einem Hintergrundbild.",
    preview: true,
  });
}
