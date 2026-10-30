import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/index.js";
import { createPinia } from "pinia";
// F29: app font, bundled by Vite from node_modules (no external CDN), so
// every computer shows the same letters. The build includes all 7 character
// subsets; the browser only downloads the ones a page uses (Latin here).
import "@fontsource-variable/inter/wght.css";
import "./index.css";

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount("#app");
