/**
 * Map module using Leaflet.js for picker and hotspot visualization.
 */

const DEFAULT_COORDS = [12.9716, 77.5946]; // Central Municipal Ward

export const MapManager = {
  pickerMap: null,
  pickerMarker: null,
  hotspotMap: null,
  hotspotLayerGroup: null,

  initPickerMap(containerId, onLocationSelect) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (this.pickerMap) {
      this.pickerMap.remove();
      this.pickerMap = null;
    }

    this.pickerMap = L.map(containerId).setView(DEFAULT_COORDS, 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(this.pickerMap);

    this.pickerMap.on("click", (e) => {
      const { lat, lng } = e.latlng;
      this.setPickerLocation(lat, lng);
      if (onLocationSelect) {
        onLocationSelect(lat, lng);
      }
    });

    // Invalidate size on container show
    setTimeout(() => this.pickerMap && this.pickerMap.invalidateSize(), 200);
  },

  setPickerLocation(lat, lng) {
    if (!this.pickerMap) return;
    if (this.pickerMarker) {
      this.pickerMarker.setLatLng([lat, lng]);
    } else {
      this.pickerMarker = L.marker([lat, lng], { draggable: true }).addTo(this.pickerMap);
      this.pickerMarker.on("dragend", (e) => {
        const pos = e.target.getLatLng();
        const latInput = document.getElementById("input-lat");
        const lngInput = document.getElementById("input-lng");
        if (latInput && lngInput) {
          latInput.value = pos.lat.toFixed(6);
          lngInput.value = pos.lng.toFixed(6);
        }
      });
    }
    this.pickerMap.panTo([lat, lng]);
  },

  initHotspotMap(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (this.hotspotMap) {
      this.hotspotMap.remove();
      this.hotspotMap = null;
    }

    this.hotspotMap = L.map(containerId).setView(DEFAULT_COORDS, 12);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; CARTO &copy; OpenStreetMap",
      maxZoom: 18,
    }).addTo(this.hotspotMap);

    this.hotspotLayerGroup = L.layerGroup().addTo(this.hotspotMap);
    setTimeout(() => this.hotspotMap && this.hotspotMap.invalidateSize(), 300);
  },

  renderHotspots(hotspots, onSelectTicket) {
    if (!this.hotspotMap || !this.hotspotLayerGroup) return;
    this.hotspotLayerGroup.clearLayers();

    const colorMap = {
      CRITICAL: "#ef4444",
      HIGH: "#f97316",
      MEDIUM: "#eab308",
      LOW: "#22c55e",
    };

    hotspots.forEach((hs) => {
      const color = colorMap[hs.highest_priority] || "#3b82f6";
      const radius = Math.min(26, 12 + hs.count * 3);

      const circle = L.circleMarker([hs.latitude, hs.longitude], {
        radius: radius,
        fillColor: color,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      });

      const popupContent = `
        <div class="p-2 text-xs">
          <div class="flex items-center justify-between mb-1 gap-2">
            <span class="font-bold text-gray-900">${hs.location_address || hs.borough}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase" style="background-color: ${color}22; color: ${color};">
              ${hs.highest_priority}
            </span>
          </div>
          <div class="text-gray-600 mb-1">
            <strong>${hs.count}</strong> complaint(s) in this cluster
          </div>
          <div class="text-gray-500 text-[11px] mb-2">
            Categories: ${hs.categories.join(", ")}
          </div>
          <div class="text-[11px] font-semibold text-gray-700">
            Max Priority Score: <span class="font-mono text-blue-600">${hs.max_priority_score}</span>
          </div>
          ${hs.complaint_ids && hs.complaint_ids.length ? `
            <button class="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-1 px-2 rounded text-[11px] transition"
              onclick="window.viewHotspotTicket('${hs.complaint_ids[0]}')">
              Inspect Lead Issue (${hs.complaint_ids[0]})
            </button>
          ` : ""}
        </div>
      `;

      circle.bindPopup(popupContent);
      this.hotspotLayerGroup.addLayer(circle);
    });
  },
};
