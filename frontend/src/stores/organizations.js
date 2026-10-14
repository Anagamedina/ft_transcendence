// STORE organizations — admin clients list, client detail, status actions and
// invitations (B1, B4, B16).

import { defineStore } from 'pinia'
import { ref } from 'vue'
import organizationsService from '../services/organizations.service.js'
import invitationsService from '../services/invitations.service.js'

// Status values of OrganizationResponse, used for the counters of the filter buttons
const STATUSES = ['TRIAL', 'ACTIVE', 'SUSPENDED']

// Same error shape as the other stores: { code, message, details }
function toStoreError(err) {
  return {
    code: err?.code,
    message: err?.message,
    details: err?.details,
  }
}

// Empty values are sent as null: the API validates emails, and '' is not a valid email
function emptyToNull(value) {
  if (typeof value !== 'string') return value ?? null
  const text = value.trim()
  return text === '' ? null : text
}

export const useOrganizationsStore = defineStore('organizations', () => {
  // STATE

  // List: one page of clients, as the API returns it (filters and pagination are server side)
  const organizations = ref([])
  const total = ref(0)
  const pages = ref(0)
  // 'idle' | 'loading' | 'success' | 'error'
  const status = ref('idle')
  const error = ref(null)

  // Number of clients per status for the filter buttons: { all, TRIAL, ACTIVE, SUSPENDED }
  const counts = ref({ all: 0, TRIAL: 0, ACTIVE: 0, SUSPENDED: 0 })

  // Detail: the client open in /admin/clients/:id
  const current = ref(null)
  const currentStatus = ref('idle')
  const currentError = ref(null)

  // Pending invitations of the current client
  const invitations = ref([])

  // Each list request gets a number; only the answer of the last one is kept,
  // so a slow answer to an old search cannot overwrite a newer one
  let lastListRequest = 0

  // ACTIONS — list

  // GET /api/organizations with the filters of the view: { status, q, page, page_size }
  async function fetchOrganizations(params = {}) {
    const request = ++lastListRequest
    status.value = 'loading'
    error.value = null

    // Only the filters that are set: the API rejects an empty status
    const query = { page: params.page ?? 1, page_size: params.page_size ?? 10 }
    if (params.status) query.status = params.status
    if (params.q && params.q.trim() !== '') query.q = params.q.trim()

    try {
      const response = await organizationsService.getOrganizations(query)
      if (request !== lastListRequest) return organizations.value

      organizations.value = response.data.items
      total.value = response.data.total
      pages.value = response.data.pages
      status.value = 'success'
      return organizations.value
    } catch (err) {
      if (request !== lastListRequest) return organizations.value

      organizations.value = []
      total.value = 0
      pages.value = 0
      error.value = toStoreError(err)
      status.value = 'error'
      throw err
    }
  }

  // Counters of the filter buttons: one small request per status (page_size 1),
  // reading only `total`. A failure keeps the previous numbers: they are secondary
  async function fetchCounts() {
    try {
      const [all, ...byStatus] = await Promise.all([
        organizationsService.getOrganizations({ page: 1, page_size: 1 }),
        ...STATUSES.map((value) =>
          organizationsService.getOrganizations({ status: value, page: 1, page_size: 1 })
        ),
      ])
      const next = { all: all.data.total }
      STATUSES.forEach((value, index) => {
        next[value] = byStatus[index].data.total
      })
      counts.value = next
    } catch {
      // Keep the last known counters
    }
  }

  // ACTIONS — detail

  async function fetchOrganization(id) {
    currentStatus.value = 'loading'
    currentError.value = null

    try {
      const response = await organizationsService.getOrganization(id)
      current.value = response.data
      currentStatus.value = 'success'
      return current.value
    } catch (err) {
      current.value = null
      currentError.value = toStoreError(err)
      currentStatus.value = 'error'
      throw err
    }
  }

  // Puts the API answer in the detail and in the list, so both views show the same data
  function replaceOrganization(updated) {
    if (current.value?.id === updated.id) current.value = updated
    organizations.value = organizations.value.map((item) => (item.id === updated.id ? updated : item))
    return updated
  }

  // ACTIONS — create and edit
  // Errors are thrown to the caller, so the form can show them without
  // turning the whole list into an error state.

  // POST /api/organizations with the wizard data: { client, site }.
  // The first building is created in the same operation (first_site): both or none.
  async function createOrganization({ client, site }) {
    const payload = {
      name: client.name.trim(),
      // AquaGuard only works in Barcelona
      city: 'Barcelona',
      contact_email: emptyToNull(client.contact_email),
      phone: emptyToNull(client.phone),
      legal_name: emptyToNull(client.legal_name),
      tax_id: emptyToNull(client.tax_id),
      billing_email: emptyToNull(client.billing_email),
    }

    if (site) {
      payload.first_site = {
        name: site.name.trim(),
        address: emptyToNull(site.address),
        floors: site.floors,
        basements: site.basements,
        building_type: site.building_type,
      }
    }

    const response = await organizationsService.createOrganization(payload)
    return response.data
  }

  // PATCH /api/organizations/{id}. data: only the fields that change
  async function updateOrganization(id, data) {
    const response = await organizationsService.updateOrganization(id, data)
    return replaceOrganization(response.data)
  }

  // ACTIONS — status changes. Each returns the updated client

  async function suspend(id) {
    const response = await organizationsService.suspend(id)
    return replaceOrganization(response.data)
  }

  async function reactivate(id) {
    const response = await organizationsService.reactivate(id)
    return replaceOrganization(response.data)
  }

  async function extendTrial(id) {
    const response = await organizationsService.extendTrial(id)
    return replaceOrganization(response.data)
  }

  async function activate(id) {
    const response = await organizationsService.activate(id)
    return replaceOrganization(response.data)
  }

  // DELETE /api/organizations/{id} with the exact name as confirmation (B16).
  // Returns what was deleted: { id, name, deleted: { sites, sensors, ... } }
  async function deleteOrganization(id, confirmName) {
    const response = await organizationsService.deleteOrganization(id, confirmName)
    organizations.value = organizations.value.filter((item) => item.id !== id)
    if (current.value?.id === id) current.value = null
    return response.data
  }

  // ACTIONS — invitations (B4, mock until its routes exist)

  // Pending invitations of one client. A failure leaves the list empty: it is secondary
  async function fetchInvitations(organizationId) {
    try {
      const response = await invitationsService.getInvitations({
        organization_id: organizationId,
        page: 1,
        page_size: 100,
      })
      invitations.value = response.data.items.filter((item) => item.status === 'PENDING')
    } catch {
      invitations.value = []
    }
    return invitations.value
  }

  // POST /api/invitations. Returns InvitationSentResponse: the only time `url` is available
  async function createInvitation({ email, organization_id }) {
    const response = await invitationsService.createInvitation({
      email: email.trim(),
      organization_id,
    })
    if (current.value?.id === organization_id) {
      invitations.value = [...invitations.value, response.data]
    }
    return response.data
  }

  return {
    organizations,
    total,
    pages,
    status,
    error,
    counts,
    current,
    currentStatus,
    currentError,
    invitations,
    fetchOrganizations,
    fetchCounts,
    fetchOrganization,
    createOrganization,
    updateOrganization,
    suspend,
    reactivate,
    extendTrial,
    activate,
    deleteOrganization,
    fetchInvitations,
    createInvitation,
  }
})
