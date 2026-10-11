// Fixtures mock of alerts
// Shape conforms to AlertResponse

export const alerts = [

  {
    id: '9c324394-8445-4ad0-8aa0-7012306865ff',
    sensor_id: '360dad3e-2fe9-44e4-a867-f145674020fd',
    sensor_name: 'Barcelo Hotel',
    site_id: '11111111-1111-4111-8111-111111111111',
    site_name: 'Depósito Norte Madrid',
    organization_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    organization_name: 'Hotel Diagonal Mar',
    floor: 0,
    type: 'HIGH_PRESSURE',
    severity: 'WARNING',
    message: 'La presión está por encima del umbral configurado.',
    status: 'ACTIVE',
    state: 'ACTIVE',
    created_at: '2026-09-08T08:20:00Z',
    acknowledged_at: null,
    resolved_at: null,
  },

  {
    id: 'ad4354a5-9556-4be1-9bb1-812341797600',
    sensor_id: '471ebe4f-3ff0-45f5-9558-2567851310aa',
    sensor_name: 'Pressure Sensor Madrid 02',
    site_id: '11111111-1111-4111-8111-111111111111',
    site_name: 'Depósito Norte Madrid',
    organization_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    organization_name: 'Hotel Diagonal Mar',
    floor: 2,
    type: 'SENSOR_OFFLINE',
    severity: 'CRITICAL',
    message: 'El sensor está desconectado.',
    status: 'ACTIVE',
    state: 'ACKNOWLEDGED',
    created_at: '2026-09-07T16:50:00Z',
    acknowledged_at: '2026-09-07T17:00:00Z',
    resolved_at: null,
  },

  {
    id: 'be5465b6-a667-4cf2-8cc2-923452808711',
    sensor_id: '582fcf50-4001-46f6-a066-3678962421bb',
    sensor_name: 'Flow Sensor Barcelona 01',
    site_id: '22222222-2222-4222-8222-222222222222',
    site_name: 'Depósito Barcelona Norte',
    organization_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    organization_name: 'Hotel Diagonal Mar',
    floor: 1,
    type: 'LOW_PRESSURE',
    severity: 'CRITICAL',
    message: 'La presión está por debajo del umbral configurado.',
    status: 'RESOLVED',
    state: 'RESOLVED',
    created_at: '2026-09-06T14:00:00Z',
    acknowledged_at: '2026-09-06T14:10:00Z',
    resolved_at: '2026-09-06T14:30:00Z',
  },

]