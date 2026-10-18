// Fixtures mock of GET /api/analytics/overview (F12)
// Shape conforms to OverviewResponse; the numbers match the other fixtures.

export const overview = {
  organizations_total: 3,
  organizations_needing_attention: 1,
  sites_total: 3,
  sensors_total: 3,
  sensors_online: 2,
  open_alerts: 2,
  critical_open_alerts: 1,
  median_resolution_minutes: 42.5,
};
