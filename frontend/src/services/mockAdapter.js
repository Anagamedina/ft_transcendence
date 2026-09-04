// MOCK ADAPTER — respuestas con el mismo contrato OpenAPI (paralelo semana 1).

const mockAdapter = {
  get(url, config = {}) {
    console.log('[MOCK GET]', url, config)

    return Promise.resolve({
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