// Fixtures mock of sensors
// Shape conforms to SensorResponse

export const sensors = [
  {
    id: '360dad3e-2fe9-44e4-a867-f145674020fd',
    site_id: '11111111-1111-4111-8111-111111111111',
    name: 'Barcelo Hotel',
    location: 'Entrada principal',
    sensor_type: 'PRESSURE',
    min_pressure: 2.0,
    max_pressure: 10.0,
    status: 'ONLINE',
    last_seen_at: '2026-09-08T08:30:00Z',
    created_at: '2026-08-05T09:00:00Z',
  },

  {
    id: '471ebe4f-3ff0-45f5-9558-2567851310aa',
    site_id: '11111111-1111-4111-8111-111111111111',
    name: 'Pressure Sensor Madrid 02',
    location: 'Sala técnica',
    sensor_type: 'PRESSURE',
    min_pressure: 1.5,
    max_pressure: 8.0,
    status: 'OFFLINE',
    last_seen_at: '2026-09-07T16:45:00Z',
    created_at: '2026-08-06T10:30:00Z',
  },

  {
    id: '582fcf50-4001-46f6-a066-3678962421bb',
    site_id: '22222222-2222-4222-8222-222222222222',
    name: 'Flow Sensor Barcelona 01',
    location: 'Zona norte',
    sensor_type: 'FLOW',
    min_pressure: 3.0,
    max_pressure: 12.0,
    status: 'ONLINE',
    last_seen_at: '2026-09-08T08:45:00Z',
    created_at: '2026-08-07T11:15:00Z',
  },
]