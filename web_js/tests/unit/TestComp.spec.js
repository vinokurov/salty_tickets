import { shallowMount } from '@vue/test-utils'
import flushPromises from 'flush-promises'
import TestComp from '@/components/TestComp.vue'
import axios from 'axios';

jest.mock('axios')
const resp = {data: 'value'};
axios.get.mockResolvedValue(resp);

describe('TestComp', () => {
  it('fetches async when a button is clicked', async () => {
    const wrapper = shallowMount(TestComp)
    wrapper.find('button').trigger('click')
    await flushPromises()
    expect(wrapper.vm.value).toBe('value')
    console.log(wrapper.vm.value)
  })


  it('fetches async when a watched field is changed', async () => {
    const wrapper = shallowMount(TestComp)
    // wrapper.find('button').trigger('click')
    wrapper.vm.state = 'AA'
    await flushPromises()
    expect(wrapper.vm.value).toBe('value')
    console.log(wrapper.vm.value)
  })
})
