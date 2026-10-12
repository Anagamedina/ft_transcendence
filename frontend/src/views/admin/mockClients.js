// TODO: temporary mock data until organizations come from the API (B1) and its store (data area).
// Shape follows OrganizationResponse from the B1 contract:
//   id, name, status (TRIAL | ACTIVE | SUSPENDED), trial_ends_at,
//   contact and billing fields, counters and created_at.
// Counters (site_count, sensor_count...) are computed by the backend;
// here they match services/fixtures/sites.js and sensors.js so the detail view stays consistent.
// It also holds mock users and functions that mimic the B1/B4/B16 endpoints, so the
// views already call "actions" with the same meaning as the future store.
// Delete this file once the organizations store exists.

import { reactive } from 'vue'
import { sites as fixtureSites } from '../../services/fixtures/sites'
import { sensors as fixtureSensors } from '../../services/fixtures/sensors'

const DAY_MS = 24 * 60 * 60 * 1000

// Days added by "extend trial" and days an invitation lasts (TRIAL_DAYS and INVITATION_TTL_DAYS)
const TRIAL_DAYS = 7
const INVITATION_TTL_DAYS = 7

// Trial end date relative to today, at 23:59:59 local time.
// Relative dates keep the demo meaningful any day: fixed dates would all be in the past soon.
// Local 23:59:59 (not UTC) so the shown end date is the intended day in Barcelona.
function trialEndsIn(days) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  date.setHours(23, 59, 59, 0)
  return date.toISOString()
}

// reactive: when an action changes a client (or a new one is created),
// every view that shows it updates without reloading
export const mockClients = reactive([
  {
    id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    name: 'Hotel Diagonal Mar',
    status: 'ACTIVE',
    trial_ends_at: null,
    city: 'Barcelona',
    contact_email: 'mantenimiento@hoteldiagonal.example.com',
    phone: '+34 600 000 001',
    legal_name: 'Hoteles Diagonal S.L.',
    tax_id: 'B12345678',
    billing_email: 'facturas@hoteldiagonal.example.com',
    site_count: 3,
    sensor_count: 3,
    user_count: 2,
    open_alerts: 1,
    critical_alerts: 1,
    created_at: '2026-08-01T08:00:00Z',
  },
  {
    id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    name: 'Escola Gràcia',
    status: 'ACTIVE',
    trial_ends_at: null,
    city: 'Barcelona',
    contact_email: 'secretaria@escolagracia.example.com',
    phone: '+34 600 000 002',
    legal_name: 'Fundació Escola Gràcia',
    tax_id: 'G23456789',
    billing_email: 'secretaria@escolagracia.example.com',
    site_count: 0,
    sensor_count: 0,
    user_count: 1,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-08-05T09:30:00Z',
  },
  {
    id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    name: 'Comunitat de veïns Sants',
    status: 'SUSPENDED',
    trial_ends_at: null,
    city: 'Barcelona',
    contact_email: 'presidencia@veinssants.example.com',
    phone: null,
    legal_name: null,
    tax_id: 'H34567890',
    billing_email: null,
    site_count: 0,
    sensor_count: 0,
    user_count: 1,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-08-10T11:00:00Z',
  },
  {
    id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    name: 'Clínica Sarrià',
    status: 'TRIAL',
    trial_ends_at: trialEndsIn(3),
    city: 'Barcelona',
    contact_email: 'direccion@clinicasarria.example.com',
    phone: '+34 600 000 004',
    legal_name: null,
    tax_id: null,
    billing_email: null,
    site_count: 0,
    sensor_count: 0,
    user_count: 1,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-10-08T10:00:00Z',
  },
  {
    // Trial already expired but still TRIAL: the admin can extend or activate it
    id: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    name: 'Restaurant del Born',
    status: 'TRIAL',
    trial_ends_at: trialEndsIn(-4),
    city: 'Barcelona',
    contact_email: 'info@restaurantborn.example.com',
    phone: '+34 600 000 005',
    legal_name: null,
    tax_id: null,
    billing_email: null,
    site_count: 0,
    sensor_count: 0,
    user_count: 1,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-09-20T12:00:00Z',
  },
  {
    id: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
    name: 'Gimnàs Poblenou',
    status: 'ACTIVE',
    trial_ends_at: null,
    city: 'Barcelona',
    contact_email: 'gerencia@gimnaspoblenou.example.com',
    phone: '+34 600 000 006',
    legal_name: 'Esports Poblenou S.L.',
    tax_id: 'B45678901',
    billing_email: 'admin@gimnaspoblenou.example.com',
    site_count: 0,
    sensor_count: 0,
    user_count: 3,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-08-29T09:00:00Z',
  },
  {
    id: '12121212-1212-4121-8121-121212121212',
    name: 'Residència Horta',
    status: 'ACTIVE',
    trial_ends_at: null,
    city: 'Barcelona',
    contact_email: 'manteniment@residenciahorta.example.com',
    phone: '+34 600 000 007',
    legal_name: 'Residència Horta S.A.',
    tax_id: 'A56789012',
    billing_email: 'comptabilitat@residenciahorta.example.com',
    site_count: 0,
    sensor_count: 0,
    user_count: 2,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-09-02T08:30:00Z',
  },
  {
    id: '34343434-3434-4343-8343-343434343434',
    name: 'Oficines Les Corts',
    status: 'TRIAL',
    trial_ends_at: trialEndsIn(1),
    city: 'Barcelona',
    contact_email: 'serveis@oficineslescorts.example.com',
    phone: null,
    legal_name: null,
    tax_id: null,
    billing_email: null,
    site_count: 0,
    sensor_count: 0,
    user_count: 1,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: '2026-10-10T16:00:00Z',
  },
])

// Users of each client. Shape follows UserResponse: id, organization_id, name, email, role, created_at.
// One line per user; the count per client matches user_count above.
export const mockUsers = reactive([
  { id: 'u-01', organization_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', name: 'Marta Soler', email: 'marta.soler@hoteldiagonal.example.com', role: 'client', created_at: '2026-08-01T09:00:00Z' },
  { id: 'u-02', organization_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', name: 'Jordi Vidal', email: 'jordi.vidal@hoteldiagonal.example.com', role: 'client', created_at: '2026-08-04T10:00:00Z' },
  { id: 'u-03', organization_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', name: 'Laia Puig', email: 'secretaria@escolagracia.example.com', role: 'client', created_at: '2026-08-05T10:00:00Z' },
  { id: 'u-04', organization_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', name: 'Pere Roca', email: 'presidencia@veinssants.example.com', role: 'client', created_at: '2026-08-10T12:00:00Z' },
  { id: 'u-05', organization_id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd', name: 'Núria Font', email: 'direccion@clinicasarria.example.com', role: 'client', created_at: '2026-10-08T11:00:00Z' },
  { id: 'u-06', organization_id: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee', name: 'Albert Serra', email: 'info@restaurantborn.example.com', role: 'client', created_at: '2026-09-20T13:00:00Z' },
  { id: 'u-07', organization_id: 'ffffffff-ffff-4fff-8fff-ffffffffffff', name: 'Clara Mas', email: 'gerencia@gimnaspoblenou.example.com', role: 'client', created_at: '2026-08-29T10:00:00Z' },
  { id: 'u-08', organization_id: 'ffffffff-ffff-4fff-8fff-ffffffffffff', name: 'Oriol Camps', email: 'oriol.camps@gimnaspoblenou.example.com', role: 'client', created_at: '2026-09-01T09:00:00Z' },
  { id: 'u-09', organization_id: 'ffffffff-ffff-4fff-8fff-ffffffffffff', name: 'Sara Ribas', email: 'sara.ribas@gimnaspoblenou.example.com', role: 'client', created_at: '2026-09-03T09:00:00Z' },
  { id: 'u-10', organization_id: '12121212-1212-4121-8121-121212121212', name: 'Anna Ferrer', email: 'manteniment@residenciahorta.example.com', role: 'client', created_at: '2026-09-02T09:30:00Z' },
  { id: 'u-11', organization_id: '12121212-1212-4121-8121-121212121212', name: 'Marc Costa', email: 'marc.costa@residenciahorta.example.com', role: 'client', created_at: '2026-09-05T09:30:00Z' },
  { id: 'u-12', organization_id: '34343434-3434-4343-8343-343434343434', name: 'Eva Martí', email: 'serveis@oficineslescorts.example.com', role: 'client', created_at: '2026-10-10T17:00:00Z' },
])

// Pending invitations (B4). A user only exists after accepting, so they do not count in user_count.
// The real invitation stores only the email; name is kept here to show who it is for.
export const mockInvitations = reactive([])

// Sites created with the wizard during this session (the fixtures cannot change)
const createdSites = reactive([])

// Sites of one client with their sensors attached, for the row expansion and the detail tabs
export function sitesOf(clientId) {
  return [...fixtureSites, ...createdSites]
    .filter((site) => site.organization_id === clientId)
    .map((site) => ({
      ...site,
      sensors: fixtureSensors.filter((sensor) => sensor.site_id === site.id),
    }))
}

export function usersOf(clientId) {
  return mockUsers.filter((user) => user.organization_id === clientId)
}

export function invitationsOf(clientId) {
  return mockInvitations.filter((invitation) => invitation.organization_id === clientId)
}

export function findClient(clientId) {
  return mockClients.find((client) => client.id === clientId)
}

// Random id in the same format as the API (UUID v4)
function newId() {
  return crypto.randomUUID()
}

// ---------------------------------------------------------------------------
// Mock actions. Same rules as the backend service (B1, B4, B16), applied locally.
// TODO: replace each one with its store action (data area).
// ---------------------------------------------------------------------------

// POST /api/organizations/{id}/suspend
export function suspendClient(client) {
  client.status = 'SUSPENDED'
}

// POST /api/organizations/{id}/reactivate: back to TRIAL if it still has a trial date
export function reactivateClient(client) {
  client.status = client.trial_ends_at ? 'TRIAL' : 'ACTIVE'
}

// POST /api/organizations/{id}/extend-trial: adds the days to the end date,
// or to today if the trial already ended
export function extendTrial(client, now = new Date()) {
  const end = new Date(client.trial_ends_at)
  const from = end > now ? end : now
  client.trial_ends_at = new Date(from.getTime() + TRIAL_DAYS * DAY_MS).toISOString()
}

// POST /api/organizations/{id}/activate: the trial becomes a paying client
export function activateClient(client) {
  client.status = 'ACTIVE'
  client.trial_ends_at = null
}

// Removes in place every item of a reactive list that matches, so views stay reactive
function removeWhere(list, matches) {
  for (let i = list.length - 1; i >= 0; i -= 1) {
    if (matches(list[i])) list.splice(i, 1)
  }
}

// DELETE /api/organizations/{id} (B16): removes the client and everything it owns
// (its users, pending invitations and the sites created in this session)
export function deleteClient(client) {
  const ownedBy = (item) => item.organization_id === client.id
  removeWhere(mockUsers, ownedBy)
  removeWhere(mockInvitations, ownedBy)
  removeWhere(createdSites, ownedBy)
  removeWhere(mockClients, (item) => item.id === client.id)
}

// POST /api/invitations (B4): returns the link the admin sends to the new user
export function inviteUser(client, { name, email }) {
  const code = Math.random().toString(36).slice(2, 8)
  const invitation = {
    id: newId(),
    organization_id: client.id,
    name,
    email,
    // Same route and param that F6 (#167) reads: /registro?invitacion=CODE (route defined by F1)
    link: `${window.location.origin}/registro?invitacion=${code}`,
    expires_at: new Date(Date.now() + INVITATION_TTL_DAYS * DAY_MS).toISOString(),
  }
  mockInvitations.push(invitation)
  return invitation
}

// POST /api/organizations with first_site, then the first invitation.
// Created by the admin, so it starts ACTIVE (the public sign-up creates trials).
export function createClient({ client, site, user }) {
  const id = newId()
  const newClient = {
    id,
    name: client.name.trim(),
    status: 'ACTIVE',
    trial_ends_at: null,
    city: 'Barcelona',
    contact_email: client.contact_email || null,
    phone: client.phone || null,
    legal_name: client.legal_name || null,
    tax_id: client.tax_id || null,
    billing_email: client.billing_email || null,
    site_count: 1,
    sensor_count: 0,
    user_count: 0,
    open_alerts: 0,
    critical_alerts: 0,
    created_at: new Date().toISOString(),
  }
  mockClients.unshift(newClient)
  createdSites.push({ id: newId(), organization_id: id, ...site, created_at: newClient.created_at })

  // Return the reactive copy, so later changes to it update every view
  const created = findClient(id)
  return { client: created, invitation: inviteUser(created, user) }
}