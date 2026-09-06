import adapter from './adapter.js'

const authService = { //creamos un objeto que agrupará todas las operaciones de autenticación
  register(data) {
    return adapter.post('/api/auth/register', data) //Cuando alguien llama a authService.register(data), se envían los datos al backend mediante POST /api/auth/register.
  },

  login(data) {
    return adapter.post('/api/auth/login', data)
  },

  logout() {
    return adapter.post('/api/auth/logout')
  },

  me() {
    return adapter.get('/api/me')
  },
}

export default authService