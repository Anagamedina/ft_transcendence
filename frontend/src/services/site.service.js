import adapter from './adapter.js'

const siteService = {
  getSites() {
    return adapter.get('/api/sites')
  },

  getSite(id) {
    return adapter.get(`/api/sites/${id}`)
  },

  getSiteSensors(id) {
    return adapter.get(`/api/sites/${id}/sensors`)
  },
}

export default siteService