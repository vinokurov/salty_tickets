import Vue from 'vue';
import Vuex from 'vuex';
import axios from 'axios'
import pathify from 'vuex-pathify';
import { make } from 'vuex-pathify';
import VueStripeCheckout from 'vue-stripe-checkout';

Vue.use(Vuex);

const my_state = {
  tickets: [],
  products: [],
  layout: {},
  event_name: '',
  registration: {
    primary: {name:null, email:null, location: null,
              dance_role:null, comments:null},
    partner: {name:null, email:null, location: null},
    partner_token:null,
    registration_token: null,
    pay_all: 'y',
  },
  cart: {
    checkout_enabled: false,
    checkout_success: null,
    items:[],
    total: 0,
    transaction_fee:0,
    pay_now_total: 0,
  },
  new_ticket_prices: [],
  stripe: {},
  errors: {},
  throttled_calls: {},
  strpe_handler: null,
  payment_response: {
    success: null,
    complete: null,
    payment_id: null,
    payee_id: null,
    error_message: null,
  },
  prior_registrations: {
    person: null,
    partner: null,
    registrations: [],
  },
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
}

export default new Vuex.Store({
  plugins: [pathify.plugin],

  state: my_state,

  mutations: {
    selectProduct (state, args) {
      state.tickets.map((p) => {if(p.key==args.key){p.choice=args.choice}})
    },
    setPricingResponseDetails (state, pricing_details) {
      state['pricing_details'] = pricing_details;
      state.cart.total = pricing_details.order_summary.total_price;
      state.cart.transaction_fee = pricing_details.order_summary.transaction_fee;
      state.cart.items = pricing_details.order_summary.items;
      state.cart.checkout_enabled = !pricing_details.disable_checkout

      state.cart.pay_now_total = pricing_details.order_summary.pay_now_total

      state.new_ticket_prices = pricing_details.new_prices;

      state.errors = pricing_details.errors;
      if('csrf_token' in state.errors){window.location.reload();}

      if(state.cart.checkout_enabled && pricing_details.stripe) {
        state.stripe = pricing_details.stripe
      } else {
        state.stripe = {}
      }
    },
    setPriorRegistrations (state, prior_registrations) {
      state['prior_registrations'] = prior_registrations;
    },
    setPaymentResponseDetails (state, payment_response) {
      state.payment_response = payment_response
    },
    queueThrottledRequest (state, {url, params}) {
      if (url in state.throttled_calls) {
          if (JSON.stringify(state.throttled_calls[url].params) != JSON.stringify(params)) {
            state.throttled_calls[url] = {
              url: url,
              params: JSON.parse(JSON.stringify(params)),
              complete: false
            }
          }
      } else {
        state.throttled_calls[url] = {
          url: url,
          params: JSON.parse(JSON.stringify(params)),
          complete: false
        }
      }
    },
    markThrottledRequestAsComplete (state, url) {
      state.throttled_calls[url].complete = true
    },
    setProductChoice(state, args){
      // console.log(args.key, this.getters.getProductByKey(args.key), args.choice)
      this.getters.getProductByKey(args.key).choice = args.choice
    },
    ...make.mutations(['registration']),
  },

  actions: {
    async initEvent ({context, state}) {
      const url = '/event/mind_the_shag_2019'
      let response = await axios.get(url)
      state.layout = response.data.layout
      state.tickets = response.data.tickets
      state.products = response.data.products
      state.event_name = response.data.name
    },
    async requestPrice({context, commit, state, getters, dispatch}) {
      const url = '/price/mind_the_shag_2019'
      let params = getters.getPricingSubmitData
      let response = await dispatch('postRequest', {url, params})
      if (response) {
        commit('setPricingResponseDetails', response.data)
        // state['pricing_details'] = response.data
      }
    },
    async requestCheckout({context, commit, state, getters, dispatch}) {
      // const url = 'http://127.0.0.1:5000/price/salty_breezle'
      const url = '/checkout/mind_the_shag_2019'
      let params = getters.getPricingSubmitData
      let response = await dispatch('postRequest', {url, params})
      if (response) {
        commit('setPricingResponseDetails', response.data)
        // state['pricing_details'] = response.data
      }
    },
    async requestPriorRegistrations({context, commit, state, getters, dispatch}) {
      // const url = 'http://127.0.0.1:5000/price/salty_breezle'
      const url = '/prior_registrations/mind_the_shag_2019'
      let params = getters.getPricingSubmitData
      let response = await dispatch('postRequest', {url, params})
      if (response) {
        commit('setPriorRegistrations', response.data)
      }
    },
    async postRequest ({ commit, state }, {url, params}) {
      commit('queueThrottledRequest', {url, params})
      return new Promise((resolve, reject) => {
        setTimeout(async () => {
          if (!state.throttled_calls[url].complete){
            if (JSON.stringify(params) === JSON.stringify(state.throttled_calls[url].params)){
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
    stripeCheckout({state, getters, commit}) {
      let panelLabel = 'Pay'
      if(state.stripe.amount == 0) {
        panelLabel = 'Save card details'
      } else if (!state.registration.pay_all) {
        panelLabel = 'Save card and pay'
      }

      this._vm.$checkout.open({
        amount: state.stripe.amount,
        email: state.stripe.email,
        name: 'Salty Jitterbugs Ltd.',
        description: state.event_name,
        currency: 'gbp',
        zipCode: true,
        billingAddress: true,
        allowRememberMe: false,
        panelLabel: panelLabel,
        token: async (token) => {
          const data = {
            stripe_token: token,
            csrf_token: getters.getCSRF,
          }
          const url = '/pay/'
          try {
            let response = await axios.post(url, data)
            commit('setPaymentResponseDetails', response.data)
          } catch(err) {
            commit('setPaymentResponseDetails', {
              success:false,
              error_message: 'Server error while processing payment',
            })
          }
        }
      })
    },
  },

  getters: {
    getTicketByKey: (state) => (key) => {
      return state.tickets.filter((p) => p.key == key)[0]
    },
    getSelectedTickets: (state) => {
      return state.tickets.filter((p) => p.choice).map((p) => ({key:p.key, choice:p.choice}))
    },
    getProductByKey: (state) => (key) => {
      return state.products.filter((p) => p.key == key)[0]
    },
    getSelectedProducts: (state) => {
      return state.products.filter((p) => p.choice).map((p) => ({key:p.key, choice:p.choice}))
    },
    getTicketNewPrice: (state) => (key) => {
      let price_items = state.new_ticket_prices.filter((p) => p.ticket_key == key)
      if(price_items.length > 0){
        return price_items[0].price
      }
    },
    getOrderedItemByKey: (state) => (key) => {
      return state.cart.items.filter((p) => p.key == key)[0]
    },
    partnerRequired: (state) => {
      return state.tickets.filter((p) => p.choice=='couple').length > 0
    },
    getPricingSubmitData: (state, getters) => {
      let data = {
        name: state.registration.primary.name || '',
        email: state.registration.primary.email || '',
        location: state.registration.primary.location || '',
        comment: state.registration.primary.comment || '',
        dance_role: state.registration.primary.dance_role || '',
        registration_token: state.registration.registration_token || '',
        generic_discount_code: state.registration.primary.discount_code || '',
        partner_name: state.registration.partner.name || '',
        partner_email: state.registration.partner.email || '',
        partner_location: state.registration.partner.location || '',
        csrf_token: getters.getCSRF,
        pay_all: state.registration.pay_all,
      }
      // ...state.products.filter((p) => p.choice).map((p) => ({key:p.key, choice:p.choice}))
      const selected = getters.getSelectedTickets
      const selected_products = getters.getSelectedProducts

      if (selected) {
        Object.keys(selected).forEach(function(key,index) {
          // key: the name of the object key
          // index: the ordinal position of the key within the object
          data[selected[key].key + '-add'] = selected[key].choice;
        });
      }
      if (selected_products) {
        Object.keys(selected_products).forEach(function(key,index) {
          // key: the name of the object key
          // index: the ordinal position of the key within the object
          data[selected_products[key].key + '-add'] = selected_products[key].choice;
        });
      }
      return data;
    },
    getCSRF: (state) => {
      let element = document.getElementById("csrf_token");
      let content = element && element.getAttribute("value");
      return content
    },
    getPriorTickets: (state, getters) => {
      let data = {}
      state.prior_registrations.registrations.forEach((reg) => {
        if(data[reg.ticket_key]){
          data[reg.ticket_key]['amount'] = 2
        } else {
          data[reg.ticket_key] = {
            ticket_key: reg.ticket_key,
            title: getters.getTicketByKey(reg.ticket_key).title,
            amount: 1
          }
        }
      })
      return data
    },
  }
});
