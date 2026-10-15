// Mock organizations (clients) for the mockAdapter. Shape follows OrganizationResponse (B1).
// Counters (site_count, sensor_count, open_alerts, critical_alerts) are NOT stored here:
// the mockAdapter computes them from the sites, sensors and alerts fixtures, as the API does.
// user_count is stored because the mock has no users table for clients.

// Trial end date relative to today, at 23:59:59 local time.
// Relative dates keep the demo meaningful any day: fixed dates would all be in the past soon.
function trialEndsIn(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  date.setHours(23, 59, 59, 0);
  return date.toISOString();
}

export const organizations = [
  {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    name: "Hotel Diagonal Mar",
    status: "ACTIVE",
    trial_ends_at: null,
    city: "Barcelona",
    contact_email: "mantenimiento@hoteldiagonal.example.com",
    phone: "+34 600 000 001",
    legal_name: "Hoteles Diagonal S.L.",
    tax_id: "B12345678",
    billing_email: "facturas@hoteldiagonal.example.com",
    user_count: 2,
    created_at: "2026-08-01T08:00:00Z",
  },
  {
    id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    name: "Escola Gràcia",
    status: "ACTIVE",
    trial_ends_at: null,
    city: "Barcelona",
    contact_email: "secretaria@escolagracia.example.com",
    phone: "+34 600 000 002",
    legal_name: "Fundació Escola Gràcia",
    tax_id: "G23456789",
    billing_email: "secretaria@escolagracia.example.com",
    user_count: 1,
    created_at: "2026-08-05T09:30:00Z",
  },
  {
    id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    name: "Comunitat de veïns Sants",
    status: "SUSPENDED",
    trial_ends_at: null,
    city: "Barcelona",
    contact_email: "presidencia@veinssants.example.com",
    phone: null,
    legal_name: null,
    tax_id: "H34567890",
    billing_email: null,
    user_count: 1,
    created_at: "2026-08-10T11:00:00Z",
  },
  {
    id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
    name: "Clínica Sarrià",
    status: "TRIAL",
    trial_ends_at: trialEndsIn(3),
    city: "Barcelona",
    contact_email: "direccion@clinicasarria.example.com",
    phone: "+34 600 000 004",
    legal_name: null,
    tax_id: null,
    billing_email: null,
    user_count: 1,
    created_at: "2026-10-08T10:00:00Z",
  },
  {
    // Trial already ended but still TRIAL: the admin can extend or activate it
    id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    name: "Restaurant del Born",
    status: "TRIAL",
    trial_ends_at: trialEndsIn(-4),
    city: "Barcelona",
    contact_email: "info@restaurantborn.example.com",
    phone: "+34 600 000 005",
    legal_name: null,
    tax_id: null,
    billing_email: null,
    user_count: 1,
    created_at: "2026-09-20T12:00:00Z",
  },
  {
    id: "ffffffff-ffff-4fff-8fff-ffffffffffff",
    name: "Gimnàs Poblenou",
    status: "ACTIVE",
    trial_ends_at: null,
    city: "Barcelona",
    contact_email: "gerencia@gimnaspoblenou.example.com",
    phone: "+34 600 000 006",
    legal_name: "Esports Poblenou S.L.",
    tax_id: "B45678901",
    billing_email: "admin@gimnaspoblenou.example.com",
    user_count: 3,
    created_at: "2026-08-29T09:00:00Z",
  },
  {
    id: "12121212-1212-4121-8121-121212121212",
    name: "Residència Horta",
    status: "ACTIVE",
    trial_ends_at: null,
    city: "Barcelona",
    contact_email: "manteniment@residenciahorta.example.com",
    phone: "+34 600 000 007",
    legal_name: "Residència Horta S.A.",
    tax_id: "A56789012",
    billing_email: "comptabilitat@residenciahorta.example.com",
    user_count: 2,
    created_at: "2026-09-02T08:30:00Z",
  },
  {
    id: "34343434-3434-4343-8343-343434343434",
    name: "Oficines Les Corts",
    status: "TRIAL",
    trial_ends_at: trialEndsIn(1),
    city: "Barcelona",
    contact_email: "serveis@oficineslescorts.example.com",
    phone: null,
    legal_name: null,
    tax_id: null,
    billing_email: null,
    user_count: 1,
    created_at: "2026-10-10T16:00:00Z",
  },
];
