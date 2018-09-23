import { shallowMount } from '@vue/test-utils'
import FontAwesome from '@/components/FontAwesome.vue'

describe('FontAwesome.vue', () => {
  it('renders icon when passed', () => {
    const icon = 'test'
    const wrapper = shallowMount(FontAwesome, { propsData: { 'icon': icon } })
    const expected_html = '<i aria-hidden="true" class="fa fa-fw fa-test"></i>'
    expect(wrapper.vm.classStr).toBe('fa fa-fw fa-test')
    expect(wrapper.html()).toBe(expected_html)
  })
})
