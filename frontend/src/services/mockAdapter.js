// MOCK ADAPTER — respuestas con el mismo contrato OpenAPI (paralelo semana 1).

import { sites } from './fixtures/sites.js'

/* We create an object that 
has the same methods as httpAdapter.
It returns a promise
that is already resolved, with the data we want,
to replicate the behavior of the real adapter*/

const mockAdapter = {

  get(url, config = {}) {
    console.log('[MOCK GET]', url, config)

    if (url === '/api/sites') { 
    return Promise.resolve({ 
      data: { // Paginated response: current page, number of items, and total pages
        items: sites,
        total: sites.length,
        page: 1,
        page_size: sites.length,
        pages: 1,
      },
      status: 200,
    })
  }

    return Promise.resolve({ // = "Create a Promise (that is already resolved) with the value below"
      data: {},
      status: 200,
    })
  },

  post(url, data = {}, config = {}) {
    console.log('[MOCK POST]', url, data, config)

    return Promise.resolve({
      data: {},
      status: 200,
    })
  },

  patch(url, data = {}, config = {}) {
    console.log('[MOCK PATCH]', url, data, config)

    return Promise.resolve({
      data: {},
      status: 200,
    })
  },

  delete(url, config = {}) {
    console.log('[MOCK DELETE]', url, config)

    return Promise.resolve({
      data: {},
      status: 200,
    })
  },
}

export default mockAdapter

/*Voici exactement ce que les services nous disent que le MockAdapter doit supporter :

Domaine	Méthode	Endpoint
Auth	POST	/api/auth/register
Auth	POST	/api/auth/login
Auth	POST	/api/auth/logout
Auth	GET	/api/me
Sites	GET	/api/sites
Sites	GET	/api/sites/{id}
Sites	GET	/api/sites/{id}/sensors
Sensors	GET	/api/sensors
Sensors	GET	/api/sensors/{id}
Sensors	POST	/api/sensors
Sensors	PATCH	/api/sensors/{id}
Readings	POST	/api/readings
Readings	GET	/api/sensors/{id}/readings
Alerts	GET	/api/alerts
Alerts	PATCH	/api/alerts/{id}/acknowledge
Alerts	PATCH	/api/alerts/{id}/resolve*/