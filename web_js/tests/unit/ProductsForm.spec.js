import { shallowMount, mount } from '@vue/test-utils'
import Vue from 'vue'
// import BootstrapVue from 'bootstrap-vue'
import ProductsForm from '@/components/RegistrationForm.vue'

// Vue.use(BootstrapVue)

describe('ProductsForm.vue', function () {

  it('getProductsLayout', () => {
    let products = {
      workshop_a1: {start_datetime: '2018-11-17 10:00:00', level: 'advanced', title: 'A1'},
      workshop_a2: {start_datetime: '2018-11-17 10:00:00', level: 'intermediate', title: 'A2'},
      workshop_b1: {start_datetime: '2018-11-17 14:00:00', level: 'advanced', title: 'B1'},
      workshop_b2: {start_datetime: '2018-11-17 14:00:00', level: 'intermediate', title: 'B2'},
      workshop_c1: {start_datetime: '2018-11-18 10:00:00', level: 'advanced', title: 'C1'},
      workshop_c2: {start_datetime: '2018-11-18 10:00:00', level: 'intermediate', title: 'C2'},
      workshop_d1: {start_datetime: '2018-11-18 14:00:00', level: 'advanced', title: 'D1'},
      workshop_d2: {start_datetime: '2018-11-18 14:00:00', level: 'intermediate', title: 'D2'},
    }
    let layout = {
      workshops: {
        Saturday: [
          {Intermediate: 'workshop_a2', Advanced: 'workshop_a1'},
          {Intermediate: 'workshop_b2', Advanced: 'workshop_b1'},
        ],
        Sunday: [
          {Intermediate: 'workshop_c2', Advanced: 'workshop_c1'},
          {Intermediate: 'workshop_d2', Advanced: 'workshop_d1'},
        ],
      }
    }
    let wrapper = shallowMount(
      RegistrationForm, {
        propsData: {
          products: products,
          layout: layout
        },
      })
  })

})
