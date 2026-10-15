import adapter from "./adapter.js";
import mockAdapter from "./mockAdapter.js";

// HTTP calls for invitations. Contract: B4 (backend/app/modules/invitations/schemas.py).
// The contract is published but the routes do not exist yet, so these calls always
// use the mockAdapter, even when the rest of the app talks to the real API.
// TODO: set to true when the B4 routes are merged into develop.
const INVITATIONS_API_READY = false;

const client = INVITATIONS_API_READY ? adapter : mockAdapter;

// The code travels inside the URL path, so it is encoded
function byCodeUrl(code) {
  return `/api/invitations/by-code/${encodeURIComponent(code)}`;
}

const invitationsService = {
  // POST /api/invitations (admin) -> InvitationSentResponse, the only time `code` and `url` are sent
  // data: { email, organization_id }
  createInvitation(data) {
    return client.post("/api/invitations", data);
  },

  // GET /api/invitations (admin) -> Page[InvitationResponse], without the code
  // params (optional): { organization_id, page, page_size }
  getInvitations(params = {}) {
    return client.get("/api/invitations", { params });
  },

  // GET /api/invitations/by-code/{code} (public) -> InvitationPublicResponse
  // { organization_name, email, expires_at }. 410 INVITATION_EXPIRED, 404 INVITATION_NOT_FOUND
  getInvitationByCode(code) {
    return client.get(byCodeUrl(code));
  },

  // POST /api/invitations/by-code/{code}/accept (public) -> 201 SessionResponse { user }
  // Creates the `client` user and opens the session, like the sign-up.
  // data: { name, password, accept_terms }. The email is the invitation's one
  acceptInvitation(code, data) {
    return client.post(`${byCodeUrl(code)}/accept`, data);
  },
};

export default invitationsService;
