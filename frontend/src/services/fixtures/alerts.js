// Fixtures mock of alerts
// Shape conforms to AlertResponse

export const alerts = [
  {
    id: '9c324394-8445-4ad0-8aa0-7012306865ff',
    sensor_id: '360dad3e-2fe9-44e4-a867-f145674020fd',
    type: 'HIGH_PRESSURE',
    severity: 'WARNING',
    message: 'Pressure is above the configured threshold.',
    status: 'ACTIVE',
    created_at: '2026-09-08T08:20:00Z',
    acknowledged_at: null,
    resolved_at: null,
  },

  {
    id: 'ad4354a5-9556-4be1-9bb1-812341797600',
    sensor_id: '471ebe4f-3ff0-45f5-9558-2567851310aa',
    type: 'SENSOR_OFFLINE',
    severity: 'CRITICAL',
    message: 'Sensor is offline.',
    status: 'ACTIVE',
    created_at: '2026-09-07T16:50:00Z',
    acknowledged_at: '2026-09-07T17:00:00Z',
    resolved_at: null,
  },

  {
    id: 'be5465b6-a667-4cf2-8cc2-923452808711',
    sensor_id: '582fcf50-4001-46f6-a066-3678962421bb',
    type: 'LOW_PRESSURE',
    severity: 'CRITICAL',
    message: 'Pressure is below the configured threshold.',
    status: 'RESOLVED',
    created_at: '2026-09-06T14:00:00Z',
    acknowledged_at: '2026-09-06T14:10:00Z',
    resolved_at: '2026-09-06T14:30:00Z',
  },
]