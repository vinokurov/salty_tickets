import { shallowMount } from '@vue/test-utils'
import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
import SwitchButton from '@/components/SwitchButton.vue'
import flushPromises from 'flush-promises'

Vue.use(BootstrapVue)

describe('SwitchButton.vue', function () {
  describe('Clicking button', function ()
    {
      let wrapper;

      beforeEach(function() {
        wrapper = shallowMount(
        	SwitchButton, {
        		propsData: {
        			'name': 'test',
        			'value': null,
              'options': [
        				{ 'checked': false, 'variant': '', 'disabled': false, 'value': 'leader', 'caption': 'Leader' },
        				{ 'checked': false, 'variant': '', 'disabled': false, 'value': 'follower', 'caption': 'Follower' },
        				{ 'checked': false, 'variant': '', 'disabled': false, 'value': 'couple', 'caption': 'Couple' }
        			],
        			'size': 'lg',
        			'editable': true,
        		}
        	});
      })

      it('button states are initialised by the attrs', function() {
        expect(wrapper.vm.button_options[0].checked).toBe(false)
        expect(wrapper.vm.button_options[1].checked).toBe(false)
        expect(wrapper.vm.button_options[2].checked).toBe(false)
      })

      it('control value is initialised by the attrs', function() {
        expect(wrapper.html()).not.toContain('input')
        expect(wrapper.vm.button_value) .toBe(null)
      })

      it('changes button states if I click another button', function() {
        expect(wrapper.vm.button_options[0].checked).toBe(false)
        expect(wrapper.vm.button_options[1].checked).toBe(false)

        wrapper.vm.ButtonClick('follower');
        expect(wrapper.vm.button_options[0].checked).toBe(false)
        expect(wrapper.vm.button_options[1].checked).toBe(true)
        expect(wrapper.vm.button_options[2].checked).toBe(false)
      })

      it('changes control value if I click another button', () => {
        wrapper.vm.ButtonClick('leader');
        expect(wrapper.html()).toContain('input')
        expect(wrapper.vm.button_value).toBe('leader')

        wrapper.vm.ButtonClick('follower');
        expect(wrapper.find('input').element.value).toBe('follower')
        expect(wrapper.vm.button_value).toBe('follower')
      })

      it('disables all buttons if I click the same button', function() {
        wrapper.vm.ButtonClick('leader');
        expect(wrapper.vm.button_options[0].checked).toBe(true)
        wrapper.vm.ButtonClick('leader');
        expect(wrapper.vm.button_options[0].checked).toBe(false)
        expect(wrapper.vm.button_options[1].checked).toBe(false)
        expect(wrapper.vm.button_options[2].checked).toBe(false)
      })

      it('sets empty value if I click the same button', () => {
        wrapper.vm.ButtonClick('leader');
        expect(wrapper.vm.button_value).toBe('leader')
        wrapper.vm.ButtonClick('leader');
        expect(wrapper.html()).not.toContain('input')
        expect(wrapper.vm.button_value).toBe(null)
      })

      it('button states aren`t affected if editable=False', function() {
        wrapper.vm.ButtonClick('leader');
        expect(wrapper.vm.button_options[0].checked).toBe(true)
        const init_button_options = JSON.parse(JSON.stringify(wrapper.vm.button_options)) // deep copy
        const init_button_value = wrapper.vm.button_value
        wrapper.setProps({editable: false})

        wrapper.vm.ButtonClick('couple');
        expect(wrapper.vm.button_options).toEqual(init_button_options)
        expect(wrapper.vm.button_value).toEqual(init_button_value)
      })

    });
})
