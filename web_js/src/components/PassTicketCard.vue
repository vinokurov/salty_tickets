<template>
    <b-card no-body :bg-variant="cardStyle.bg" :text-variant="cardStyle.text"
                    :border-variant="cardStyle.border" class="text-left">
        <div class="card-body">
            <div class="d-flex justify-content-between">
              <h5 class="card-title"><font-awesome icon="lock" v-if="!editable"/> {{title}}</h5>
              <span class="h5"><b-badge pill variant="secondary">£ {{price}}</b-badge></span>
            </div>
            <slot></slot>
            <switch-button
                  :name="inputName"
                  :options="buttonOptions"
                  :editable="editable"
                  value="workshopChoice"
                  v-model="workshopChoice"
                  size="sm"
                  v-if="!soldOut"
                  />
        </div>
        <div class="card-footer">
        </div>
    </b-card>
</template>

<script>
import BootstrapVue from 'bootstrap-vue'
import FontAwesome from './FontAwesome.vue'
import SwitchButton from './SwitchButton.vue'

export default {
  name: 'PassTicketCard',
  components: {FontAwesome, SwitchButton, BootstrapVue},
  props: {
    inputName: { type: String },
    icon: { default: 'ticket', type: String },
  },
  data: function () {
    return {
      workshopChoice: this.choice,
    }
  },
  methods: {
    capitalize(string)
    {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
  },
  computed: {
    product: function(){
      return this.$store.getters.getTicketByKey(this.inputName)
    },
    title: function() { return this.product.title },
    price: function() { return this.product.price },
    available: function() { return this.product['available'] || 'plenty'},
    choice: function() { return this.product.choice },
    lines: function() { return this.product.lines || '' },
    partnerMode: function() { return  null },
    editable: function() { return this.product.editable || true },

    cardStyle: function () {
      if (this.soldOut) {
        return {bg: 'secondary', border: '', text: 'black'}
      } else if (this.workshopChoice ) {
        return {bg: 'success', border: '', text: 'light'}
      } else {
        return {bg: 'light', border:'', text: 'black'}
      }
    },
    availableWarningStyle: function () {
      if (this.available <= 0) {
        return 'light'
      } else {
        return 'danger'
      }
    },
    availableWarningText: function () {
      if (this.available > 5) {
        return ''
      } else if (this.available <= 0) {
        return 'SOLD OUT...'
      } else if (this.available == 1) {
        return 'LAST PLACE!!!'
      } else {
        return 'Just ' + this.available + ' places left!'
      }
    },
    soldOut: function () {
      return this.available <= 0
    },
    buttonOptions: function () {
      if (this.partnerMode == 'single') {
        if (this.workshopChoice == 'couple') this.workshopChoice = 'leader'
      } else if (this.partnerMode == 'couple') {
        if (this.workshopChoice) this.workshopChoice = 'couple'
      }

      let buttons = [
        {
          variant: 'dark-green',
          caption: 'Single',
          value: 'leader',
          state: this.workshopChoice == 'leader',
          disabled: false
        },
        {
          variant: 'dark-green',
          caption: 'Couple',
          value: 'couple',
          state: this.workshopChoice == 'couple',
          disabled: false
        },
      ]

      if (this.soldOut) {
        for (let i = 0; i < buttons.length; i++) {
          buttons[i].disabled = true
        }
      }

      // partner mode: single, couple or none
      if (this.partnerMode == 'single') {
        buttons[0].disabled = false
        buttons[1].disabled = true
      } else if (this.partnerMode == 'couple') {
        buttons[0].disabled = true
        buttons[1].disabled = false
      } else {
        buttons[0].disabled = false
        buttons[1].disabled = false
      }

      return buttons
    }
  },
  watch: {
    choice: function() {
      this.workshopChoice = this.choice;
    },
    workshopChoice: function () {
      this.$store.commit(
        'selectProduct',
        {key: this.inputName, choice: this.workshopChoice}
      )
    }
  },
}
</script>
