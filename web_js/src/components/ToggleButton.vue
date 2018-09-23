<template>
  <b-button :variant="btnVariant"
            :class="btnClass" :pressed.sync="btnPressed"
            @click="$emit('input', btnPressed)">
    <slot></slot>
  </b-button>
</template>

<script>
export default {
  props: {
    variant: { type: String },
    pressed: { type: Boolean, default:false },
  },
  data: function() {
    return {
      btnPressed: this.pressed,
    }
  },
  watch: {
    pressed: function() {
      this.btnPressed = this.pressed;
    }
  },
  computed: {
    btnVariant: function () {
      if (this.btnPressed) {
        return this.variant
      } else {
        return 'outline-' + this.variant
      }
    },
    btnClass: function () {
      if (this.btnPressed) {
        return "toggle-on"
      } else {
        return "toggle-off"
      }
    }
  },
}
</script>

<style>
.toggle-on {
  margin-left: 6px; margin-right:6px; margin-top:6px; margin-bottom:6px;
}
.toggle-off {
  margin-left: 4px; margin-right:4px; margin-top:6px; margin-bottom:6px;
}
</style>
