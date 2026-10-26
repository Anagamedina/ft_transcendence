import adapter from "./adapter.js";

// HTTP calls for "Hazte cliente". Contract: B14
// (PlanResponse / SubscriptionRequest / SubscriptionResponse).
const subscriptionsService = {
  // GET /api/plans -> PlanResponse[]. Public, no session needed.
  getPlans() {
    return adapter.get("/api/plans");
  },

  // POST /api/me/organization/subscribe. The client's TRIAL organization
  // becomes ACTIVE. 409 ORGANIZATION_NOT_IN_TRIAL if it is not in trial;
  // 422 TERMS_NOT_ACCEPTED, INVALID_TAX_ID or INVALID_IBAN.
  subscribe(data) {
    return adapter.post("/api/me/organization/subscribe", data);
  },
};

export default subscriptionsService;
