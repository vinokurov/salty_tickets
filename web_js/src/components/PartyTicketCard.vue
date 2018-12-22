<template>
    <b-card no-body :bg-variant="cardStyle.bg" :text-variant="cardStyle.text"
                    :border-variant="cardStyle.border" class="text-left shadow ">
        <div class="card-body">
            <div class="d-flex justify-content-between">
              <h5 class="card-title"><font-awesome icon="lock" v-if="!product.editable"/> {{title}}</h5>
              <span v-if="!disabled">
                <span class="h4" v-if="paid_price != null">£{{paid_price}}</span>
                <span v-else-if="special_price != null"><span class="h4">£{{special_price}}</span><br/><small><strike>£{{price}}</strike></small></span>
                <span class="h4" v-else>£{{price}}</span>
              </span>
            </div>
            {{product.info}}
            <switch-button
                  :name="inputName"
                  :options="buttonOptions"
                  :editable="product.editable"
                  value="workshopChoice"
                  v-model="workshopChoice"
                  size="sm"
                  v-if="!disabled"
                  />
        </div>
        <div class="card-footer">
          <p style="margin:0" v-if="time">
            <small :class="'text-' + cardStyle.text_footer"><font-awesome icon="clock"/> {{time}}</small>
          </p>
          <p style="margin:0" v-if="location">
            <small :class="'text-' + cardStyle.text_footer"><font-awesome icon="map-marker-alt"/> {{location}}</small>
          </p>
        </div>
    </b-card>
</template>

<script>
import BootstrapVue from 'bootstrap-vue'
import FontAwesome from './FontAwesome.vue'
import SwitchButton from './SwitchButton.vue'
import { mapState, mapActions,mapGetters } from 'vuex'

export default {
  name: 'PartyTicketCard',
  components: {FontAwesome, SwitchButton, BootstrapVue},
  props: {
    inputName: { type: String },
    icon: { default: 'ticket', type: String },
    special_price: {type: Number, default: null}
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
    time: function() {
      let dt0 = new Date(this.product.start_datetime)
      let dt1 = new Date(this.product.end_datetime)
      return dt0.toLocaleTimeString().replace(':00', '') + ' - ' + dt1.toLocaleTimeString().replace(':00', '')
    },
    choice: function() { return this.product.choice },
    location: function() { return this.product.location },
    // lines: function() { return this.product.lines || '' },
    partnerMode: function() { return  null },
    editable: function() { return this.product.editable || true },

    cardStyle: function () {
      if (this.disabled) {
        return {bg: 'secondary', border: '', text: 'black', text_footer:'black'}
      } else if (this.workshopChoice ) {
        return {bg: 'gradient-success', border: '', text: 'light', text_footer:'light'}
      } else {
        return {bg: 'light', border:'', text: 'black', text_footer:'muted'}
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
    disabled: function() {
      return this.soldOut || ((this.choice == null) && this.product.editable == false )
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
    },
    paid_price: function(){
      var item = this.getOrderedItemByKey(this.inputName)
      if (item != null) return item.price
    },
    ...mapGetters(['getOrderedItemByKey']),
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
