// API FACADE — punto único de llamadas HTTP.
// Flujo: View/Store → api.js → MockAdapter | HttpAdapter (mismo shape OpenAPI).

our te documenter, je te conseille cet ordre :

HTTP / REST → comprendre comment Vue communique avec FastAPI.
Axios → comprendre ce qu’il apporte par rapport à fetch.
Service / couche de service → comprendre pourquoi on ne met pas les appels API dans les composants.
Adapter Pattern → comprendre pourquoi vous avez HttpAdapter et MockAdapter.
Interceptors Axios → comprendre les headers, erreurs, authentification, 401, etc.
Gestion centralisée des erreurs.
Mock → comprendre pourquoi on veut pouvoir remplacer le vrai backend.

Et surtout, ne cherche pas à tout apprendre en profondeur avant de commencer. Pour ton issue, il suffit d'abord de comprendre le rôle de chaque concept.

Le schéma mental à retenir

Imagine :

LoginView.vue
     │
     │ "connecte cet utilisateur"
     ↓
authService
     │
     │ POST /login
     ↓
HttpAdapter
     │
     ↓
Axios
     │
     ↓
FastAPI

Le composant Vue ne devrait pas savoir comment la requête est envoyée.

Et plus tard, pour les tests :

authService
     │
     ↓
HttpAdapter
     │
     ├──── Axios → FastAPI
     │
     └──── Mock  → fausses données

C'est essentiellement ça que ton issue cherche à construire.