import Vue from 'vue';
import Vuex from 'vuex';
import axios from 'axios'
import pathify from 'vuex-pathify';
import { make } from 'vuex-pathify';
import VueStripeCheckout from 'vue-stripe-checkout';

Vue.use(Vuex);

const my_state = {
  event_info: {
    name: null,
    key: null,
    products: [],
    layout: null,
    registrations: [],
    payments: [],
  }
}

// const stripe_pk = document.getElementById("stripe_pk").getAttribute("value");
// const csrf = document.getElementById("csrf_token").getAttribute("value");
const event_key = document.getElementById("event_key").getAttribute("value");

export default new Vuex.Store({
  plugins: [pathify.plugin],

  state: my_state,

  mutations: {},

  getters: {},

  actions: {
    async init ({context, state}) {
      const url = '/admin/event_info/' + event_key
      let response = await axios.get(url)
      console.log(response.data)
      state.event_info = response.data
    },
  },
})
