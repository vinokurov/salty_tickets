import Vue from 'vue';
import Vuex from 'vuex';
import axios from 'axios'
import pathify from 'vuex-pathify';
import { make } from 'vuex-pathify';
import VueStripeCheckout from 'vue-stripe-checkout';

Vue.use(Vuex);

const my_state = {
  user_order_info: {
    products: [],
    name: null,
    email: null,
    ptn_token: null,
    total_paid:null,
    remaining_to_pay:null,
  }
}

// const stripe_pk = document.getElementById("stripe_pk").getAttribute("value");
// const csrf = document.getElementById("csrf_token").getAttribute("value");
const pmt_token = document.getElementById("pmt_token").getAttribute("value");

export default new Vuex.Store({
  plugins: [pathify.plugin],

  state: my_state,

  mutations: {},

  getters: {},

  actions: {
    async init ({context, state}) {
      const url = '/order_info/' + pmt_token
      let response = await axios.get(url)
      console.log(response.data)
      state.user_order_info = response.data
    },
  },
})
