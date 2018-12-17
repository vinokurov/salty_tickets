<template>
    <b-card no-body class="text-left shadow ">
        <div class="card-header">
          <div class="d-flex justify-content-between">
            <h5 class="card-title"> {{title}}</h5>
            <span class="h5"><b-badge pill variant="secondary">£ {{price}}</b-badge></span>
          </div>

        </div>

        <div>
          <b-carousel id="carousel1"
                      style="text-shadow: 1px 1px 2px #333;"
                      controls
                      indicators
                      background="#ababab"
                      :interval="4000"
                      img-width="200"
                      img-height="200"
          >
          <b-carousel-slide :img-src="i.url" v-for="i in image_urls">
            {{i.text}}
          </b-carousel-slide>
          </b-carousel>
        </div>

        <div class="card-body">
            <slot></slot>
            <b-input-group class="my-2">
              <b-form-select v-model="selected" style="background-image: none">
                <option :value="null">Select an option</option>
                <option :value="opt" v-for="text, opt in options">{{text}}</option>
              </b-form-select>
              <!-- <b-form-input type="number" v-model="amount"></b-form-input> -->
              <b-btn size="sm" @click="add" :disabled="!selected">Add</b-btn>
            </b-input-group>
        </div>
        <div class="card-footer">
          <b-list-group v-if="choice">
            <b-list-group-item variant="success" size="sm" class="text-small" v-for="opt_amount, opt in choice">
              {{options[opt]}} x {{opt_amount}}
              <b-btn size="sm" @click="remove(opt)" class="close">
                <font-awesome icon="times"/>
              </b-btn>
            </b-list-group-item>
          </b-list-group>
        </div>
    </b-card>
</template>

<script>
import BootstrapVue from 'bootstrap-vue'
import FontAwesome from './FontAwesome.vue'
import SwitchButton from './SwitchButton.vue'

export default {
  name: 'MerchandiseProductCard',
  components: {FontAwesome, BootstrapVue},
  props: {
    inputName: { type: String },
    icon: { default: 'ticket', type: String },
  },
  data: function () {
    return {
      selected: null,
      amount: 1,
    }
  },
  mounted() {
    if(Object.keys(this.options).length == 1) {
      this.selected = Object.keys(this.options)[0]
    }
  },
  computed: {
    product: function(){
      return this.$store.getters.getProductByKey(this.inputName)
    },
    title: function() { return this.product.title },
    price: function() { return this.product.price },
    available: function() { return this.product['available'] || 'plenty'},
    options: function() { return this.product.options},
    image_urls: function() { return this.product.image_urls},
    choice: function() { return this.product.choice},
    // editable: function() { return this.product.editable || true },
  },
  methods: {
    add: function(){
      let choice_copy = this.choice
      if (choice_copy[this.selected]) choice_copy[this.selected] += 1
      else choice_copy[this.selected] = 1
      // choice_copy[this.selected] = this.amount
      let optionKey = this.selected
      this.$store.commit('setProductChoice', {key:this.inputName, choice:choice_copy})
      this.selected = null
      this.$store.dispatch('requestPrice');
      this.selected = optionKey
    },
    remove: function(key) {
      let choice_copy = this.choice
      delete choice_copy[key]
      // this.choice = choice_copy
      console.log(choice_copy)
      this.$store.commit('setProductChoice', {key:this.inputName, choice:choice_copy})
      this.selected = null
      this.$store.dispatch('requestPrice');
      this.selected = key
    },

    // add: function(){
    //   this.choices.append({this.selected: this.amount})
    // },
    // remove: function(item) {
    //   this.choices = this.choices.splice(this.choices.indexOf(item), 1)
    // }

  },
}
</script>
