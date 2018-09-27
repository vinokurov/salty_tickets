import Vue from 'vue';
import Vuex from 'vuex';
import axios from 'axios'
import pathify from 'vuex-pathify';
import { make } from 'vuex-pathify';
import VueStripeCheckout from 'vue-stripe-checkout';

Vue.use(Vuex);

const my_state = {
  products: [],
  layout: {},
  registration: {
    primary: {name:null, email:null, location: null,
              dance_role:null, comments:null},
    partner: {name:null, email:null, location: null},
    partner_token:null,
  },
  cart: {checkout_enabled: false, checkout_success: null, items:[], total: 0, transaction_fee:0},
  stripe: {},
  errors: {},
  throttled_calls: {},
  strpe_handler: null,
}


const stripe_field = document.getElementById("stripe_pk");
if (stripe_field) {
  const checkout_base_options = {
    key: stripe_field.value,
    locale: 'auto',
    currency: 'gbp',
    billingAddress: true,
    panelLabel: 'Pay'
  }

  Vue.use(VueStripeCheckout, checkout_base_options);
  console.log('REGISTERED STRIPE WITH:')
  console.log(checkout_base_options)
}

export default new Vuex.Store({
  plugins: [pathify.plugin],

  state: my_state,

  mutations: {
    selectProduct (state, args) {
      state.products.map((p) => {if(p.key==args.key){p.choice=args.choice}})
    },
    setPricingResponseDetails (state, pricing_details) {
      state['pricing_details'] = pricing_details;
      state.cart.total = pricing_details.order_summary.total_price;
      state.cart.transaction_fee = pricing_details.order_summary.transaction_fee;
      state.cart.items = pricing_details.order_summary.items;
      state.cart.checkout_enabled = !pricing_details.disable_checkout

      state.errors = pricing_details.errors;
      if('csrf_token' in state.errors){window.location.reload();}

      if(state.cart.checkout_enabled && pricing_details.stripe) {
        state.stripe = pricing_details.stripe
      } else {
        state.stripe = {}
      }
    },
    queueThrottledRequest (state, {url, params}) {
      if (url in state.throttled_calls) {
          if (state.throttled_calls[url].params != params) {
            state.throttled_calls[url] = {
              url: url,
              params: params,
              complete: false
            }
          }
      } else {
        state.throttled_calls[url] = {
          url: url,
          params: params,
          complete: false
        }
      }
    },
    markThrottledRequestAsComplete (state, url) {
      state.throttled_calls[url].complete = true
    },
    ...make.mutations(['registration']),
  },

  actions: {
    async initEvent ({context, state}) {
      // const url = 'http://127.0.0.1:5000/event/salty_breezle'
      const url = '/event/salty_breezle'
      let response = await axios.get(url)
      console.log(response.data)
      state.layout = response.data.layout
      state.products = response.data.products
    },
    async requestPrice({context, commit, state, getters, dispatch}) {
      // const url = 'http://127.0.0.1:5000/price/salty_breezle'
      const url = '/price/salty_breezle'
      let params = getters.getPricingSubmitData
      let response = await dispatch('postRequest', {url, params})
      if (response) {
        console.log(response.data)
        commit('setPricingResponseDetails', response.data)
        // state['pricing_details'] = response.data
      }
    },
    async requestCheckout({context, commit, state, getters, dispatch}) {
      // const url = 'http://127.0.0.1:5000/price/salty_breezle'
      const url = '/checkout/salty_breezle'
      let params = getters.getPricingSubmitData
      let response = await dispatch('postRequest', {url, params})
      if (response) {
        console.log(response.data)
        commit('setPricingResponseDetails', response.data)
        // state['pricing_details'] = response.data
      }
    },
    async postRequest ({ commit, state }, {url, params}) {
      commit('queueThrottledRequest', {url, params})
      return new Promise((resolve, reject) => {
        setTimeout(async () => {
          if (!state.throttled_calls[url].complete){
            if (params == state.throttled_calls[url].params){
              console.log('QUERY: ' + url)
              let response = await axios.post(url, state.throttled_calls[url].params)
              commit('markThrottledRequestAsComplete', url)
              resolve(response)
            } else {
              resolve()
            }
          }
          resolve()
        }, 1000)
      })
    },
    stripeCheckout({state, getters}) {
      this._vm.$checkout.open({
        amount: state.stripe.amount,
        email: state.stripe.email,
        name: 'Salty Jitterbugs Ltd.',
        description: 'Event name',
        currency: 'gbp',
        zipCode: true,
        billingAddress: true,
        allowRememberMe: false,
        token: async (token) => {
          console.log('STRIPE RECEIVED')
          console.log(token)
          const data = {
            stripe_token: token,
            csrf_token: getters.getCSRF,
          }
          console.log(data)
          const url = '/pay/'
          let response = await axios.post(url, data)
          console.log(response)
        }
      })
    },
  },

  getters: {
    getProductByKey: (state) => (key) => {
      return state.products.filter((p) => p.key == key)[0]
    },
    getSelectedProducts: (state) => {
      return state.products.filter((p) => p.choice).map((p) => ({key:p.key, choice:p.choice}))
    },
    partnerRequired: (state) => {
      return state.products.filter((p) => p.choice=='couple').length > 0
    },
    getPricingSubmitData: (state, getters) => {
      let data = {
        name: state.registration.primary.name || '',
        email: state.registration.primary.email || '',
        location: state.registration.primary.location || '',
        comment: state.registration.primary.comment || '',
        dance_role: state.registration.primary.dance_role || '',
        partner_name: state.registration.partner.name || '',
        partner_email: state.registration.partner_email || '',
        partner_location: state.registration.partner.location || '',
        csrf_token: getters.getCSRF,
      }
      // ...state.products.filter((p) => p.choice).map((p) => ({key:p.key, choice:p.choice}))
      const selected = getters.getSelectedProducts
      if (selected) {
        Object.keys(selected).forEach(function(key,index) {
          // key: the name of the object key
          // index: the ordinal position of the key within the object
          data[selected[key].key + '-add'] = selected[key].choice;
        });
      }
      return data;
    },
    getCSRF: (state) => {
      let element = document.getElementById("csrf_token");
      let content = element && element.getAttribute("value");
      console.log(content);
      return content
    },
  }
});
