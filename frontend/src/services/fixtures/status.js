// Fixture mock of the status page
// Shape conforms to StatusResponse

export const systemStatus = {
  status: 'DEGRADED',
  checked_at: '2026-10-10T10:00:00Z',
  components: [
    { name: 'backend', status: 'OPERATIONAL', last_event_at: null, size_bytes: null },
    { name: 'database', status: 'OPERATIONAL', last_event_at: null, size_bytes: null },
    { name: 'simulator', status: 'DOWN', last_event_at: '2026-10-10T08:12:00Z', size_bytes: null },
    { name: 'backup', status: 'OPERATIONAL', last_event_at: '2026-10-10T03:00:00Z', size_bytes: 48213 },
  ],
}
