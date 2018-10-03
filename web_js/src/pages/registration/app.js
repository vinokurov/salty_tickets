import Vue from 'vue';
import App from './App.vue';
import store from './store';
import BootstrapVue from 'bootstrap-vue'

Vue.config.productionTip = true;
Vue.use(BootstrapVue)

new Vue({
  store: store,
  render: h => h(App),
}).$mount('#app');
