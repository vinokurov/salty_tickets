import { shallowMount, mount } from '@vue/test-utils'
import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
import WorkshopCard from '@/components/WorkshopCard.vue'

Vue.use(BootstrapVue)

describe('WorkshopCard.vue', function () {

  it('mounts', () => {

    let wrapper = mount(
      WorkshopCard, {
        propsData: {
          title: 'My Workshop' ,
          inputName: 'my_workshop',
          price: '£25',
          available: 15,
          time: '10:00',
          teachers: 'Mr. X & Ms. Y'
        },
        slots: {
          default: 'My workshop info'
        }
      })
  })

})
