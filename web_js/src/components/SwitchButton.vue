<template>
  <div>
    <!-- <b-button-group :size="size"> -->
      <toggle-button v-for="btn in button_options"
                :variant="btn.variant"
                :disabled="btn.disabled"
                :pressed="btn.state"
                v-model="btn.state"
                @input="toggle(btn.value, btn.state)"
      >{{ btn.caption }}</toggle-button>
    <!-- </b-button-group> -->
    <input type="hidden" :name="name" :value="button_value" v-if="button_value">
  </div>
</template>

<script>
import ToggleButton from './ToggleButton.vue';
export default {
  name: 'SwitchButton',
  components: {ToggleButton},
  props: {
    'name': String,
    'value': String,
    'options': Array,
    'size': String,
    'editable': Boolean
  },
  data: function() {
    return {
      button_options: this.options,
      button_value: this.value,
    }
  },
  watch: {
    button_value: function () {
      for (let i = 0; i < this.button_options.length; i++) {
        this.button_options[i].state = (this.button_options[i].value == this.button_value)
      }
      this.$emit('input', this.button_value);
      this.$emit('change', this.button_value);
    },
  },
  methods: {
    toggle: function (value, state){
        if (state) {
          this.button_value = value;
        } else {
          this.button_value = ''
        }
    }
  }
}
</script>
