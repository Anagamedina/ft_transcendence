<!-- CLIENT DASHBOARD — sensores propios, histórico Chart.js, alertas. -->



<script setup>
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'

const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()
</script>