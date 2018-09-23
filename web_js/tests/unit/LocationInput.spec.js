import { mount, shallowMount } from '@vue/test-utils'
import Vue from 'vue'
import flushPromises from 'flush-promises'
import BootstrapVue from 'bootstrap-vue'
import LocationInput from '@/components/LocationInput.vue'
import axios from 'axios';

Vue.use(BootstrapVue)

jest.mock('axios')

describe('LocationInput.vue', function () {
    let wrapper;
    let inputText;

    beforeEach(function () {
      wrapper = shallowMount(
      	LocationInput, {
      		propsData: { 'name': 'test_location' }
        })
        inputText = wrapper.find('input');
    });

    afterEach(function ()  {
      // moxios.uninstall()
    })

    it('uses flushPromises', async (done) => {

      const response = {
        data: [{'display_name': 'London, UK, MOXIOS', 'moxios': true}],
        status:200
      }
      axios.get.mockResolvedValue(response);

      wrapper.setData({queryText: 'London'})
      expect(wrapper.vm.queryText).toBe('London');

      const input_1 = wrapper.findAll('input').wrappers[1]
      const input_0 = wrapper.findAll('input').wrappers[0]

      // debugger
      await flushPromises()
      expect(wrapper.vm.locationText).toContain('London, UK')

      expect(input_1.element.value).toBe('London')
      expect(input_0.element.value).toBe(JSON.stringify(response.data[0]))

      const form_group = wrapper.find('bformgroup-stub')
      expect(form_group.element.attributes['state'].value).toBe('true')
      expect(form_group.element.attributes['validfeedback'].value)
        .toBe('Location found: London, UK, MOXIOS')
      expect(form_group.element.attributes['invalidfeedback'].value)
        .toBe('')
      done()

    })

  })
