<!--
  SITES MAP
  Reusable MapLibre map with a FIXED overview of the city of Barcelona, rotated like
  tourist maps (sea at the bottom, Collserola at the top), so the admin always sees
  all clients at a glance (no zoom, no panning).
  - Official municipal boundary outlined, everything outside it faded.
  - Marker colour shows the site's alert level (none / warning / critical).
  Only the map and its legend: the parent decides where it goes (card, modal...).
  interactive = false: fixed overview (no zoom, no panning).
  interactive = true : zoom and panning allowed, but never further out than the whole
                       city nor outside it; a button brings back the whole city.
  Receives sites via props only (no HTTP calls).
  Each site needs: id, name, latitude, longitude.
  Optional: address (shown in popup), alertLevel: 'none' | 'warning' | 'critical',
  organization_name (client name, shown first in the popup and tooltip).
  Emits: select-site(site) when "Ver detalle" is clicked (only with selectable).
-->

<template>
  <div>
    <!-- Legend -->
    <ul class="flex flex-wrap justify-end gap-4 mb-3 text-xs text-gray-500">
      <li class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-full bg-aqua-400 border border-aqua-600"></span> Sin alertas
      </li>
      <li class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-full bg-warning border border-amber-600"></span> Aviso
      </li>
      <li class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-full bg-danger border border-red-700"></span> Crítica
      </li>
    </ul>

    <!-- relative z-0: keeps the map's internal z-indexes inside this box,
         so the map never covers the mobile Sidebar (z-40) or Modal (z-50). -->
    <div class="relative z-0">
      <div
        ref="mapContainer"
        class="w-full rounded-lg overflow-hidden"
        :style="{ height }"
      ></div>

      <button
        v-if="interactive && zoomedIn"
        type="button"
        class="absolute top-3 left-3 z-10 bg-white text-aqua-600 text-sm font-semibold px-3 py-1.5 rounded-lg shadow-md border border-gray-200 hover:bg-aqua-50 transition"
        @click="fitCity(true)"
      >
        Ver toda la ciudad
      </button>

      <p
        v-if="validSites.length === 0"
        class="absolute inset-0 z-10 flex items-center justify-center bg-white/70 text-sm text-gray-500"
      >
        No hay sites con ubicación para mostrar.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// Official municipal boundary of Barcelona (Ajuntament de Barcelona / CartoBCN, CC-BY),
// simplified. Imported as a static file: bundled by Vite, no HTTP call.
import barcelonaLimit from '../assets/geo/barcelona-limit.json'

const props = defineProps({
  sites: { type: Array, default: () => [] },
  height: { type: String, default: '560px' },
  // GeoJSON of the area to show. Default: the city of Barcelona
  boundary: { type: Object, default: () => barcelonaLimit },
  // -45: coast horizontal, sea at the bottom, Collserola at the top
  bearing: { type: Number, default: -45 },
  // Fraction of the area (from the top of the rotated map) left out of the frame.
  // 0 = the whole municipality (default). E.g. 0.3 hides most of Collserola forest.
  // Sites are never left out.
  cropTop: { type: Number, default: 0 },
  // true: allow zoom and panning (inside the city). false: fixed overview
  interactive: { type: Boolean, default: false },
  // true: the popup shows a "Ver detalle" button that emits 'select-site'.
  // The parent decides what to do (e.g. navigate): the map has no router inside.
  selectable: { type: Boolean, default: false },
})

const emit = defineEmits(['select-site'])

// Free base map, no API key: OpenFreeMap "Liberty" (coloured style, OpenStreetMap data)
const MAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'
const PADDING = 16

// Marker look per alert level (Tailwind classes from the AquaGuard palette)
const MARKER_CLASSES = {
  none: 'bg-aqua-400 border-aqua-600',
  warning: 'bg-warning border-amber-600',
  critical: 'bg-danger border-red-700 animate-pulse',
}
const ALERT_TEXT = {
  warning: 'Aviso activo',
  critical: 'Alerta crítica activa',
}

const mapContainer = ref(null)
// true when the user has zoomed in (shows the "Ver toda la ciudad" button)
const zoomedIn = ref(false)

// Map objects are kept OUT of Vue reactivity on purpose:
// wrapping them in ref() makes Vue proxy MapLibre internals and breaks it.
let map = null
let markers = []
let resizeObserver = null
let mapReady = false
let fittedZoom = null // zoom that shows the whole city: the user cannot zoom out further

// Only sites with real numeric coordinates can be drawn
const validSites = computed(() =>
  props.sites.filter(
    (s) => Number.isFinite(Number(s.latitude)) && Number.isFinite(Number(s.longitude))
  )
)

// All outer rings of the boundary, as [lng, lat] (GeoJSON order)
const boundaryRings = computed(() => {
  const rings = []
  props.boundary.features.forEach((feature) => {
    const geom = feature.geometry
    const polygons = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates
    polygons.forEach((polygon) => rings.push(polygon[0]))
  })
  return rings
})

// Lng/lat box of the boundary: sites outside it are not used to frame the map
const boundaryBox = computed(() => {
  const pts = boundaryRings.value.flat()
  return {
    minLng: Math.min(...pts.map((p) => p[0])),
    maxLng: Math.max(...pts.map((p) => p[0])),
    minLat: Math.min(...pts.map((p) => p[1])),
    maxLat: Math.max(...pts.map((p) => p[1])),
  }
})

// Popup built with textContent (not an HTML string) so data coming
// from the API can never inject HTML.
function buildPopup(site, level) {
  const box = document.createElement('div')
  // Client (organization) name first, when the parent provides it
  if (site.organization_name) {
    const client = document.createElement('p')
    client.className = 'text-base font-bold text-aqua-900'
    client.textContent = site.organization_name
    box.appendChild(client)
  }
  const name = document.createElement('p')
  name.className = site.organization_name ? 'text-sm font-semibold text-gray-700' : 'font-semibold text-gray-800'
  name.textContent = site.name
  box.appendChild(name)
  if (site.address) {
    const address = document.createElement('p')
    address.className = 'text-sm text-gray-500'
    address.textContent = site.address
    box.appendChild(address)
  }
  if (ALERT_TEXT[level]) {
    const alert = document.createElement('p')
    alert.className = `mt-1 text-sm font-semibold ${level === 'critical' ? 'text-danger' : 'text-amber-600'}`
    alert.textContent = ALERT_TEXT[level]
    box.appendChild(alert)
  }
  if (props.selectable) {
    const button = document.createElement('button')
    button.type = 'button'
    button.className =
      'mt-2 w-full bg-aqua-600 text-white text-sm font-semibold px-3 py-1.5 rounded-md hover:bg-aqua-800 transition'
    button.textContent = 'Ver detalle'
    button.addEventListener('click', () => emit('select-site', site))
    box.appendChild(button)
  }
  return box
}

function drawMarkers() {
  if (!map) return
  markers.forEach((m) => m.remove())
  markers = validSites.value.map((site) => {
    const level = MARKER_CLASSES[site.alertLevel] ? site.alertLevel : 'none'
    const el = document.createElement('div')
    el.className = `w-[18px] h-[18px] rounded-full border-2 shadow-md cursor-pointer ${MARKER_CLASSES[level]}`
    el.title = site.organization_name ? `${site.organization_name} · ${site.name}` : site.name
    return new maplibregl.Marker({ element: el })
      .setLngLat([Number(site.longitude), Number(site.latitude)]) // MapLibre: [lng, lat]
      .setPopup(new maplibregl.Popup({ offset: 12 }).setDOMContent(buildPopup(site, level)))
      .addTo(map)
  })
}

// Frames the rotated city as tightly as possible in the box.
// (fitBounds only knows north-up lat/lng rectangles, which are too big once rotated.)
function fitCity(animate = false) {
  if (!map || !mapReady) return
  map.resize()
  const width = map.getContainer().clientWidth - 2 * PADDING
  const height = map.getContainer().clientHeight - 2 * PADDING
  if (width <= 0 || height <= 0) return

  // Rotate Mercator coordinates the same way the screen is rotated
  const phi = (-props.bearing * Math.PI) / 180
  const cos = Math.cos(phi)
  const sin = Math.sin(phi)
  const rotate = (lng, lat) => {
    const m = maplibregl.MercatorCoordinate.fromLngLat([lng, lat])
    return [m.x * cos - m.y * sin, m.x * sin + m.y * cos]
  }

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  const extend = ([x, y]) => {
    minX = Math.min(minX, x); maxX = Math.max(maxX, x)
    minY = Math.min(minY, y); maxY = Math.max(maxY, y)
  }
  boundaryRings.value.flat().forEach(([lng, lat]) => extend(rotate(lng, lat)))

  // Crop the top (Collserola forest)...
  minY += (maxY - minY) * props.cropTop
  // ...but never leave out a site that is inside the city
  const box = boundaryBox.value
  validSites.value
    .map((s) => [Number(s.longitude), Number(s.latitude)])
    .filter(([lng, lat]) => lng >= box.minLng && lng <= box.maxLng && lat >= box.minLat && lat <= box.maxLat)
    .forEach(([lng, lat]) => extend(rotate(lng, lat)))

  // 512 = size of the world in pixels at zoom 0 in MapLibre
  const zoom = Math.log2(Math.min(width / ((maxX - minX) * 512), height / ((maxY - minY) * 512)))
  // Centre of the rotated box, rotated back to normal Mercator coordinates
  const cx = (minX + maxX) / 2
  const cy = (minY + maxY) / 2
  const center = new maplibregl.MercatorCoordinate(cx * cos + cy * sin, -cx * sin + cy * cos).toLngLat()
  fittedZoom = zoom
  if (props.interactive) map.setMinZoom(zoom) // never further out than the whole city
  const view = { center, zoom, bearing: props.bearing, pitch: 0 }
  if (animate) map.easeTo({ ...view, duration: 800 })
  else map.jumpTo(view)
}

// Interactive mode: if the centre goes out of the city, bring it back inside
function keepInsideCity() {
  if (!map) return
  const box = boundaryBox.value
  const { lng, lat } = map.getCenter()
  const clampedLng = Math.min(Math.max(lng, box.minLng), box.maxLng)
  const clampedLat = Math.min(Math.max(lat, box.minLat), box.maxLat)
  if (clampedLng !== lng || clampedLat !== lat) {
    map.easeTo({ center: [clampedLng, clampedLat], duration: 300 })
  }
}

function drawBoundary() {
  // Mask: the whole world with the city cut out as "holes", faded.
  // Mercator maps cannot draw the poles: ±85° is their real limit.
  const world = [[-180, -85], [180, -85], [180, 85], [-180, 85], [-180, -85]]
  map.addSource('city-mask', {
    type: 'geojson',
    data: { type: 'Feature', geometry: { type: 'Polygon', coordinates: [world, ...boundaryRings.value] } },
  })
  map.addLayer({
    id: 'city-mask',
    type: 'fill',
    source: 'city-mask',
    paint: { 'fill-color': '#f1f5f9', 'fill-opacity': 0.88 },
  })

  // Outline of the city
  map.addSource('city-limit', { type: 'geojson', data: props.boundary })
  map.addLayer({
    id: 'city-limit',
    type: 'line',
    source: 'city-limit',
    paint: { 'line-color': '#0369a1', 'line-width': 2 }, // aqua-600
  })
}

onMounted(() => {
  map = new maplibregl.Map({
    container: mapContainer.value,
    style: MAP_STYLE,
    center: [2.16, 41.39],
    zoom: 11.5,
    bearing: props.bearing,
    attributionControl: { compact: true, customAttribution: 'Límite: Ajuntament de Barcelona (CC-BY)' },
    // Zoom/pan only in interactive mode. Rotation and tilt are always off,
    // so the map keeps its orientation (sea at the bottom).
    dragPan: props.interactive,
    scrollZoom: props.interactive,
    doubleClickZoom: props.interactive,
    touchZoomRotate: props.interactive,
    keyboard: props.interactive,
    boxZoom: false,
    dragRotate: false,
    touchPitch: false,
    pitchWithRotate: false,
  })

  if (props.interactive) {
    map.touchZoomRotate.disableRotation()
    map.keyboard.disableRotation()
    // + / − buttons (no compass: the map cannot be rotated)
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.on('moveend', keepInsideCity)
    map.on('zoom', () => {
      zoomedIn.value = fittedZoom !== null && map.getZoom() > fittedZoom + 0.05
    })
  }

  map.on('load', () => {
    mapReady = true
    drawBoundary()
    fitCity()
  })
  drawMarkers()

  // Keep the whole city visible when the window/box is resized (e.g. mobile, sidebar)
  resizeObserver = new ResizeObserver(() => {
    // Interactive and zoomed in: keep the user's view, only adapt the size
    if (props.interactive && zoomedIn.value) map.resize()
    else fitCity()
  })
  resizeObserver.observe(mapContainer.value)
})

// New list of sites (e.g. the store finished loading, or an alert changed a colour)
watch(
  validSites,
  () => {
    drawMarkers()
    fitCity()
  },
  { deep: true }
)

// Free map resources when leaving the page
onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
  markers.forEach((m) => m.remove())
  markers = []
  if (map) {
    map.remove()
    map = null
  }
})
</script>
