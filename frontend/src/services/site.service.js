import httpAdapter from './httpAdapter.js'

const siteService = {
  getSites() {
    return httpAdapter.get('/api/sites')
  },

  getSite(id) {
    return httpAdapter.get(`/api/sites/${id}`)
  },

  getSiteSensors(id) {
    return httpAdapter.get(`/api/sites/${id}/sensors`)
  },
}

export default siteService