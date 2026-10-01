<!--
  SITES MAP
  Reusable Leaflet + OpenStreetMap map. Receives sites via props only (no HTTP calls).
  Each site needs: id, name, latitude, longitude (address is optional, shown in popup).
-->

<template>
  <section class="bg-white border border-gray-200 rounded-xl shadow-md p-5">
    <div class="flex items-center gap-2 mb-4">
      <span class="w-5 h-5 text-aqua-600"><AppIcon name="building" /></span>
      <h2 class="text-lg font-bold text-gray-800">{{ title }}</h2>
    </div>

    <!-- relative z-0: keeps Leaflet's internal z-indexes (up to 1000) inside this box,
         so the map never covers the mobile Sidebar (z-40) or Modal (z-50). -->
    <div class="relative z-0">
      <div
        ref="mapContainer"
        class="w-full rounded-lg overflow-hidden"
        :style="{ height }"
      ></div>

      <p
        v-if="validSites.length === 0"
        class="absolute inset-0 z-[1000] flex items-center justify-center bg-white/70 text-sm text-gray-500"
      >
        No hay sites con ubicación para mostrar.
      </p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  sites: { type: Array, default: () => [] },
  title: { type: String, default: 'Mapa de sites' },
  height: { type: String, default: '400px' },
  // Fallback view when there are no sites: Barcelona (AquaGuard's target city)
  defaultCenter: { type: Array, default: () => [41.3874, 2.1686] },
  defaultZoom: { type: Number, default: 12 },
})

const mapContainer = ref(null)

// Leaflet objects are kept OUT of Vue reactivity on purpose:
// wrapping them in ref() makes Vue proxy Leaflet internals and breaks it.
let map = null
let markersLayer = null

// Only sites with real numeric coordinates can be drawn
const validSites = computed(() =>
  props.sites.filter(
    (s) => Number.isFinite(Number(s.latitude)) && Number.isFinite(Number(s.longitude))
  )
)

// Popup built with textContent (not an HTML string) so names coming
// from the API can never inject HTML.
function buildPopup(site) {
  const box = document.createElement('div')
  const name = document.createElement('p')
  name.className = 'font-semibold text-gray-800'
  name.textContent = site.name
  box.appendChild(name)
  if (site.address) {
    const address = document.createElement('p')
    address.className = 'text-sm text-gray-500'
    address.textContent = site.address
    box.appendChild(address)
  }
  return box
}

function drawMarkers() {
  if (!map) return
  markersLayer.clearLayers()

  const points = validSites.value.map((site) => {
    const latLng = [Number(site.latitude), Number(site.longitude)]
    // circleMarker is drawn with SVG: no image files, so it avoids the classic
    // "broken marker icon" problem of Leaflet + Vite, and uses AquaGuard colours.
    L.circleMarker(latLng, {
      radius: 9,
      color: '#0369a1', // aqua-600
      weight: 2,
      fillColor: '#06b6d4', // aqua-400
      fillOpacity: 0.85,
    })
      .bindPopup(buildPopup(site))
      .bindTooltip(site.name)
      .addTo(markersLayer)
    return latLng
  })

  if (points.length === 1) {
    map.setView(points[0], 13)
  } else if (points.length > 1) {
    map.fitBounds(L.latLngBounds(points), { padding: [30, 30] })
  } else {
    map.setView(props.defaultCenter, props.defaultZoom)
  }
}

onMounted(() => {
  map = L.map(mapContainer.value).setView(props.defaultCenter, props.defaultZoom)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)
  drawMarkers()
})

// Redraw when the parent sends a new list (e.g. when the store finishes loading)
watch(validSites, drawMarkers, { deep: true })

// Free Leaflet resources when leaving the page
onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>
