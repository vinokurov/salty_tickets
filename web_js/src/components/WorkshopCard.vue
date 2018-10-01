<template>
    <b-card no-body :bg-variant="cardStyle.bg" :text-variant="cardStyle.text"
                    :border-variant="cardStyle.border" class="text-left">
        <div class="card-body">
            <span class="close" :id="inputName + '-info'"><font-awesome icon="info-circle"/></span>
            <b-popover :target="inputName + '-info'" triggers="click blur"><slot></slot></b-popover>
            <h5 class="card-title"><font-awesome icon="lock" v-if="!editable"/> {{title}}</h5>
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
            <p style="margin:0" v-if="time">
              <small class="text-muted"><font-awesome icon="clock-o"/> {{time}}</small>
            </p>
            <p style="margin:0" v-if="teachers">
              <small class="text-muted"><font-awesome icon="id-badge"/> {{teachers}}</small>
            </p>
            <p style="margin:0" v-if="level">
              <small class="text-muted"><font-awesome icon="tachometer"/> {{capitalize(level)}}</small>
            </p>
            <p style="margin:0" v-if="availableWarningText">
              <b-badge :variant="availableWarningStyle">
                <font-awesome icon="exclamation-circle"/> {{availableWarningText}}
              </b-badge>
            </p>
        </div>
    </b-card>
</template>

<script>
import BootstrapVue from 'bootstrap-vue'
import FontAwesome from './FontAwesome.vue'
import SwitchButton from './SwitchButton.vue'

export default {
  name: 'WorkshopCard',
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
      return this.$store.getters.getProductByKey(this.inputName)
    },
    title: function() { return this.product.title },
    price: function() { return this.product.price },
    available: function() { return this.product['available'] || 'plenty'},
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
      if (this.soldOut) {
        return {bg: 'secondary', border: '', text: 'black'}
      } else if (this.workshopChoice ) {
        let wl = this.product.waiting_list[this.workshopChoice]
        if (wl == null) {
          return {bg: 'success', border: '', text: 'light'}
        } else {
          return {bg: 'warning', border: '', text: 'light'}
        }
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
        buttons[0].variant = 'warning'
      }
      if (this.product.waiting_list.follower != null) {
        buttons[1].variant = 'warning'
      }
      if (this.product.waiting_list.couple != null) {
        buttons[2].variant = 'warning'
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
