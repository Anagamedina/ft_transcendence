import httpAdapter from './httpAdapter.js'

const authService = { //creamos un objeto que agrupará todas las operaciones de autenticación
  register(data) {
    return httpAdapter.post('/api/auth/register', data) //Cuando alguien llama a authService.register(data), se envían los datos al backend mediante POST /api/auth/register.
  },

  login(data) {
    return httpAdapter.post('/api/auth/login', data)
  },

  logout() {
    return httpAdapter.post('/api/auth/logout')
  },

  me() {
    return httpAdapter.get('/api/me')
  },
}

export default authService