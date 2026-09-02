<!-- ADMIN DASHBOARD — KPIs, mapa Leaflet, sitios/sensores/alertas. -->


<script setup>
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'

const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()
</script>