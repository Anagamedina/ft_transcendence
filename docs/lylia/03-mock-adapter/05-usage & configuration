# 5. Usage & Configuration

## Overview

The frontend supports two adapters:

- `MockAdapter` for frontend development without a running backend.
- `HttpAdapter` for communication with the real backend API.

Both adapters expose the same interface, so frontend components and services do not need to change when switching between them.

The adapter is selected through the `VITE_USE_MOCK` environment variable.

## Configuration

### Use the MockAdapter

Set the following variable in `.env`:

```env
VITE_USE_MOCK=true
```

The frontend will use the local mock data instead of making requests to the backend.

### Use the real API

Set:

```env
VITE_USE_MOCK=false
```

The frontend will use the `HttpAdapter` and communicate with the configured backend.

The API URL is configured with:

```env
VITE_API_URL=http://localhost:8000
```

Restart the frontend after changing environment variables.

## Adapter Selection

The adapter is selected centrally:

```js
const adapter =
  import.meta.env.VITE_USE_MOCK === 'true'
    ? mockAdapter
    : httpAdapter
```

Services always use the common adapter:

```js
import adapter from './adapter.js'
```

They do not need to know whether the `MockAdapter` or `HttpAdapter` is being used.

## Available Fixtures

Mock data is stored in the `fixtures` directory:

```text
fixtures/
├── sites.js
├── sensors.js
├── readings.js
└── alerts.js
```

### Sites

`fixtures/sites.js` contains site data including:

- `id`
- `organization_id`
- `name`
- `address`
- `latitude`
- `longitude`
- `created_at`

### Sensors

`fixtures/sensors.js` contains sensor data including:

- `id`
- `site_id`
- `name`
- `location`
- `sensor_type`
- `min_pressure`
- `max_pressure`
- `status`
- `last_seen_at`
- `created_at`

### Readings

`fixtures/readings.js` contains sensor pressure readings including:

- `id`
- `sensor_id`
- `pressure`
- `measured_at`
- `created_at`

### Alerts

`fixtures/alerts.js` contains alert data including:

- `id`
- `sensor_id`
- `type`
- `severity`
- `message`
- `status`
- `created_at`
- `acknowledged_at`
- `resolved_at`

## Supported Mock Endpoints

### Authentication

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/me
```

### Sites

```text
GET /api/sites
GET /api/sites/{id}
GET /api/sites/{id}/sensors
```

### Sensors

```text
GET   /api/sensors
POST  /api/sensors
GET   /api/sensors/{id}
PATCH /api/sensors/{id}
```

### Readings

```text
POST /api/readings
GET  /api/sensors/{id}/readings
```

### Alerts

```text
GET   /api/alerts
PATCH /api/alerts/{id}/acknowledge
PATCH /api/alerts/{id}/resolve
```

## Simulated Scenarios

The `MockAdapter` provides several scenarios required for frontend development and testing.

### Successful Requests

Successful responses use the same response structure as the API, including:

- `data`
- `status`

Paginated endpoints return the following structure:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 1,
  "pages": 0
}
```

### Empty Data

The mock includes sites with no sensors to allow empty-state development and testing.

### 404 Errors

Invalid resource IDs return normalized errors such as:

```js
{
  status: 404,
  code: 'SITE_NOT_FOUND',
  message: 'Site not found',
  details: null
}
```

Similar errors are provided for sensors and alerts.

### 401 Errors

Authentication state is simulated.

After logout, `/api/me` returns:

```js
{
  status: 401,
  code: 'UNAUTHORIZED',
  message: 'Authentication required.',
  details: null
}
```

### 422 Validation Errors

The mock validates important input constraints, such as:

- pressure values outside `0–25` bar;
- invalid sensor pressure thresholds.

Example:

```js
{
  status: 422,
  code: 'VALIDATION_ERROR',
  message: 'Invalid request.',
  details: [...]
}
```

## In-Memory Persistence

Some mock operations update the fixture data in memory during the current application session.

For example:

- creating a sensor makes it available to subsequent requests;
- creating a reading makes it available when fetching sensor readings;
- acknowledging an alert updates `acknowledged_at`;
- resolving an alert updates its status and `resolved_at`;
- updating a sensor changes its current values.

The data is reset when the application is restarted.

## Development Workflow

During frontend development, use:

```env
VITE_USE_MOCK=true
```

This allows views and components to be developed without requiring the backend to be available.

When backend integration is ready, switch to:

```env
VITE_USE_MOCK=false
```

The same services and frontend components are then used with the real API.

No component changes should be required when switching adapters.

## Important Rule

Fixtures must not be imported directly by Vue components or services.

The expected flow is:

```text
Components
    ↓
Services
    ↓
Common Adapter
    ↙       ↘
MockAdapter  HttpAdapter
    ↓           ↓
Fixtures     Backend API
```

This keeps the mock implementation isolated and ensures that frontend code remains compatible with the real API.

## Verification

The `MockAdapter` has been verified against the agreed API contracts.

The verification covers:

- successful requests;
- empty results;
- invalid IDs;
- authentication state;
- validation errors;
- sensor creation and updates;
- reading creation and retrieval;
- alert acknowledgement and resolution;
- response and pagination shapes;
- switching between `MockAdapter` and `HttpAdapter`.

The frontend can therefore be developed using the `MockAdapter` and switched to the real API without rewriting the views.