<template>
  <div id="checkout" class="sticky-top bg-dark py-1 mb-1 align-middle">
      <div class="container align-middle">
          <div class="row align-middle">
              <div class="col-3 align-middle">
                <h3 class="display-5 align-middle">
                  <a class="text-white align-middle">
                     Total: £{{cart.total.toFixed(0)}}
                   </a>
                 </h3>
               </div>
              <div class="col">
                  <button type="button"
                          class="btn btn-dark btn-outline-light"
                          @click="requestCheckout"
                          v-b-modal.checkoutModal>
                      <font-awesome icon="shopping-cart" aria-hidden="true"/>
                      <span class="checkout-text">({{cart.items.length}}) Checkout</span>
                  </button>
              </div>
          </div>
      </div>

    <b-modal  size="lg" id="checkoutModal" hide-footer title="Checkout">
      <div class="d-block">
        <b-list-group v-if="Object.keys(errors).length">
          <b-list-group-item v-for="(error, error_key) in errors" variant="danger">
            {{error_key}}: {{error[0]}}
          </b-list-group-item>
        </b-list-group>
          <!-- <h3><font-awesome icon="shopping-cart"/> Order Summary</h3> -->
          <b-list-group>
            <b-list-group-item v-for="item in cart.items" class="d-flex justify-content-between align-items-center">
              {{itemFormat(item)}}<div v-if="item.price">£{{item.price.toFixed(2)}}</div>
            </b-list-group-item>
            <b-list-group-item class="d-flex justify-content-between align-items-center small font-italic font-weight-light">
              Transaction fee <div>£{{cart.transaction_fee.toFixed(2)}}</div>
            </b-list-group-item>
            <b-list-group-item variant="primary" class="d-flex justify-content-between align-items-center font-weight-bold">
              Total <div>£{{(cart.transaction_fee + cart.total).toFixed(2)}}</div>
            </b-list-group-item>
          </b-list-group>
          <button class="btn btn-success my-4" @click="stripeCheckout()" v-if="cart.checkout_enabled">
            <font-awesome icon="credit-card"/> Sign up and pay
          </button>
      </div>
    </b-modal>
  </div>
</template>

<script>
import { mapState, mapActions,mapGetters } from 'vuex'
import FontAwesome from './FontAwesome.vue'

export default {
  components: {FontAwesome},
  computed: {
    ...mapState(['cart', 'errors']),
  },
  methods: {
    itemFormat(item) {
      let values = [item.name]
      if (item.person) {values.push(item.person)}
      if (item.dance_role) {values.push(item.dance_role)}
      console.log(values, values.join(' / '))
      return values.join(' / ')
    },
    ...mapActions(['requestPrice', 'requestCheckout', 'stripeCheckout'])
  },
}
</script>
