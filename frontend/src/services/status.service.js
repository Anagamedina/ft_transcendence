import adapter from './adapter.js'

const statusService = {
  getStatus() {
    return adapter.get('/api/status')
  },
}

export default statusService
