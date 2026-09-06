// MOCK ADAPTER — respuestas con el mismo contrato OpenAPI (paralelo semana 1).


/* We create an object that 
has the same methods as httpAdapter.
It returns a promise
that is already resolved, with the data we want,
to replicate the behavior of the real adapter*/

const mockAdapter = {
  get(url, config = {}) {
    console.log('[MOCK GET]', url, config)

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