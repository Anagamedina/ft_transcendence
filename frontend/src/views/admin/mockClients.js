// TODO: temporary mock data until organizations come from the store/API (#121, data area).
// Shape follows OrganizationResponse: id, name (max 120 chars), created_at.
// Delete this file once the organizations store exists.

export const mockClients = [
  {
    id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    name: 'Hotel Diagonal Mar',
    created_at: '2026-08-01T08:00:00Z',
  },
  {
    id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    name: 'Escola Gràcia',
    created_at: '2026-08-05T09:30:00Z',
  },
  {
    id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    name: 'Comunitat de veïns Sants',
    created_at: '2026-08-10T11:00:00Z',
  },
]