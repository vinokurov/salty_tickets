<template>
    <b-card no-body :bg-variant="cardStyle.bg" :text-variant="cardStyle.text"
                    :border-variant="cardStyle.border" class="text-left shadow ">
        <div class="card-header text-light" :style="'background-color: '+headerColor">
          <span class="close" :id="inputName + '-info'"><font-awesome icon="info-circle"/></span>
          <b-popover :target="inputName + '-info'" triggers="click blur">{{product.info}}</b-popover>
          <h5 class="card-title"><font-awesome icon="lock" v-if="!product.editable"/> {{title}}</h5>
        </div>
        <div class="card-body">
            <switch-button
                  :name="inputName"
                  :options="buttonOptions"
                  :editable="product.editable"
                  :value="workshopChoice"
                  v-model="workshopChoice"
                  size="sm"
                  v-if="!disabled"
                  />
        </div>
        <span v-if="(this.product.key != 'shag_clinic') && (!disabled)">
          <b-alert v-if="this.product.waiting_list.leader !== null" show variant="warning">
            <font-awesome icon="exclamation-triangle"/> Waiting list for leaders.<br/>
            Chances to get accepted: {{this.product.waiting_list.leader}}%.
          </b-alert>
          <b-alert v-if="this.product.waiting_list.follower !== null" show variant="warning">
            <font-awesome icon="exclamation-triangle"/> Waiting list for followers.<br/>
            Chances to get accepted: {{this.product.waiting_list.follower}}%.
          </b-alert>
        </span>
        <div class="card-footer d-flex justify-content-between align-items-end" >
          <span>
            <p style="margin:0" v-if="time">
              <small :class="'text-' + cardStyle.text_footer"><font-awesome icon="clock"/> {{time}}</small>
            </p>
            <p style="margin:0" v-if="teachers">
              <small :class="'text-' + cardStyle.text_footer"><font-awesome icon="id-badge"/> {{teachers}}</small>
            </p>
            <p style="margin:0" v-if="level">
              <small :class="'text-' + cardStyle.text_footer"><font-awesome icon="tachometer-alt"/> {{capitalize(level)}}</small>
            </p>
            <p style="margin:0" v-if="availableWarningText">
              <b-badge :variant="availableWarningStyle">
                <font-awesome icon="exclamation-circle"/> {{availableWarningText}}
              </b-badge>
            </p>
          </span>
          <span v-if="!disabled">
            <span class="h4" v-if="paid_price != null">£{{paid_price}}</span>
            <span v-else-if="special_price != null"><span class="h4">£{{special_price}}</span><br/><small><strike>£{{price}}</strike></small></span>
            <span class="h4" v-else>£{{price}}</span>
          </span>
        </div>
    </b-card>
</template>

<script>
import BootstrapVue from 'bootstrap-vue'
import FontAwesome from './FontAwesome.vue'
import SwitchButton from './SwitchButton.vue'
import { mapState, mapActions,mapGetters } from 'vuex'

export default {
  name: 'WorkshopCard',
  components: {FontAwesome, SwitchButton, BootstrapVue},
  props: {
    inputName: { type: String },
    icon: { default: 'ticket', type: String },
    headerColor: { type: String, default: '#5D6D7E'},
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
    available: function() { return this.product['available']},
    time: function() {
      let dt0 = new Date(this.product.start_datetime)
      let dt1 = new Date(this.product.end_datetime)
      return dt0.toLocaleTimeString().replace(':00', '') + ' - ' + dt1.toLocaleTimeString().replace(':00', '')
    },
    teachers: function() { return this.product.teachers },
    level: function() { return this.product.level },
    choice: function() { return this.product.choice },
    lines: function() { return this.product.lines || '' },
    partnerMode: function() { return  null },
    editable: function() { return this.product.editable || true },

    cardStyle: function () {
      if (this.disabled) {
        return {bg: 'secondary', border: '', text: 'black', text_footer:'black'}
      } else if (this.workshopChoice ) {
        let wl = this.product.waiting_list[this.workshopChoice]
        if (wl == null) {
          return {bg: 'gradient-success', border: '', text: 'light', text_footer:'light'}
        } else {
          return {bg: 'gradient-warning', border: '', text: 'light', text_footer:'light'}
        }
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
      if (this.available > 10) {
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

      let buttons = []
      let roles = ['leader', 'follower', 'couple']
      for (let i=0; i<roles.length; i++ ) {
        buttons.push({
          variant: 'dark-green',
          caption: this.capitalize(roles[i]),
          value: roles[i],
          state: this.workshopChoice == roles[i],
          disabled: false
        })
      }

      if (this.soldOut) {
        for (let i = 0; i < buttons.length; i++) {
          buttons[i].disabled = true
        }
      }

      if (this.product.waiting_list.leader != null) {
        buttons[0].variant = 'dark-orange'
        buttons[0].chances = this.product.waiting_list.leader
      }
      if (this.product.waiting_list.follower != null) {
        buttons[1].variant = 'dark-orange'
        buttons[1].chances = this.product.waiting_list.follower
      }
      if (this.product.waiting_list.couple != null) {
        buttons[2].variant = 'dark-orange'
        buttons[2].chances = this.product.waiting_list.couple
      }

      // partner mode: single, couple or none
      if (this.partnerMode == 'single') {
        buttons[0].disabled = false
        buttons[1].disabled = false
        buttons[2].disabled = true
      } else if (this.partnerMode == 'couple') {
        buttons[0].disabled = true
        buttons[1].disabled = true
        buttons[2].disabled = false
      } else {
        buttons[0].disabled = false
        buttons[1].disabled = false
        buttons[2].disabled = false
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
