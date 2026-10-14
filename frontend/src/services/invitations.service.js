import adapter from './adapter.js'
import mockAdapter from './mockAdapter.js'

// HTTP calls for invitations. Contract: B4 (backend/app/modules/invitations/schemas.py).
// The contract is published but the routes do not exist yet, so these calls always
// use the mockAdapter, even when the rest of the app talks to the real API.
// TODO: set to true when the B4 routes are merged into develop.
const INVITATIONS_API_READY = false

const client = INVITATIONS_API_READY ? adapter : mockAdapter

const invitationsService = {
  // POST /api/invitations (admin) -> InvitationSentResponse, the only time `code` and `url` are sent
  // data: { email, organization_id }
  createInvitation(data) {
    return client.post('/api/invitations', data)
  },

  // GET /api/invitations (admin) -> Page[InvitationResponse], without the code
  // params (optional): { organization_id, page, page_size }
  getInvitations(params = {}) {
    return client.get('/api/invitations', { params })
  },
}

export default invitationsService
