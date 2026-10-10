import httpAdapter from './httpAdapter.js'
import mockAdapter from './mockAdapter.js'

const adapter = import.meta.env.VITE_USE_MOCK === 'true' ? mockAdapter : httpAdapter

export default adapter