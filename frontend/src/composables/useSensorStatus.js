// Traduce el estado técnico de un sensor (normal | warning | critical | offline)
// a su representación visual: label, icono y clases de color.
// Centralizado aquí para que SensorCard, la vista de detalle y, más adelante,
// Alertas usen siempre la misma traducción — nunca decide umbrales, solo traduce
// un status que ya llega calculado desde fuera (mock o API).

const STATUS_MAP = {
  normal: {
    label: 'Normal',
    icon: '✅',
    textClass: 'text-success',
    bgClass: 'bg-success/10',
    borderClass: 'border-success'
  },
  warning: {
    label: 'Alerta',
    icon: '⚠️',
    textClass: 'text-warning',
    bgClass: 'bg-warning/10',
    borderClass: 'border-warning'
  },
  critical: {
    label: 'Crítico',
    icon: '🚨',
    textClass: 'text-danger',
    bgClass: 'bg-danger/10',
    borderClass: 'border-danger'
  },
  offline: {
    label: 'Sin conexión',
    icon: '📡',
    textClass: 'text-gray-500',
    bgClass: 'bg-gray-100',
    borderClass: 'border-gray-300'
  }
}

export function useSensorStatus(status) {
  return STATUS_MAP[status] || STATUS_MAP.offline
}
