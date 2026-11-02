// Fixtures mock of sites
// Shape conforms to SiteResponse (B2): organization_name, floors, basements,
// building_type, sensor_count and status are what the API returns today.
// district is optional: the API adds it after B2 (D10); null means "not known yet".
// sensor_count matches fixtures/sensors.js.

export const sites = [
  {
    id: "11111111-1111-4111-8111-111111111111",
    organization_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    organization_name: "Hotel Diagonal Mar",
    name: "Torre Diagonal Mar",
    address: "Avinguda Diagonal, 100, Barcelona",
    latitude: 41.4096,
    longitude: 2.2169,
    floors: 4,
    basements: 2,
    building_type: "HOTEL",
    district: "SANT_MARTI",
    sensor_count: 2,
    status: "CRITICAL",
    created_at: "2026-08-01T08:00:00Z",
  },

  {
    id: "22222222-2222-4222-8222-222222222222",
    organization_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    organization_name: "Hotel Diagonal Mar",
    name: "Edificio Eixample",
    address: "Carrer de Mallorca, 401, Barcelona",
    latitude: 41.4036,
    longitude: 2.1744,
    floors: 6,
    basements: 1,
    building_type: "OFFICE",
    district: "EIXAMPLE",
    sensor_count: 1,
    status: "WARNING",
    created_at: "2026-08-01T08:00:00Z",
  },

  {
    id: "33333333-3333-4333-8333-333333333333",
    organization_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    organization_name: "Hotel Diagonal Mar",
    name: "Edificio Poblenou",
    address: "Carrer de Pujades, 150, Barcelona",
    latitude: 41.4005,
    longitude: 2.199,
    floors: 2,
    basements: 0,
    building_type: "OTHER",
    district: null,
    sensor_count: 0,
    status: "OK",
    created_at: "2026-08-03T10:15:00Z",
  },
];
