<template>
  <div id="checkout" class="sticky-top bg-dark py-1 mb-1 ">
      <div class="container">
          <div class="row">
              <div class="col-auto mr-auto">
                <h3 class="display-5 text-white">Total: £{{cart.total.toFixed(0)}}</h3>
              </div>
              <div class="col-auto">
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

    <b-modal  size="lg" id="checkoutModal" ref="checkoutModal" hide-footer title="Checkout">
      <div class="d-block">
        <b-list-group v-if="Object.keys(errors).length">
          <b-list-group-item v-for="(error, error_key) in errors" variant="danger">
            {{error_key}}: {{error[0]}}
          </b-list-group-item>
        </b-list-group>
          <!-- <h3><font-awesome icon="shopping-cart"/> Order Summary</h3> -->
          <b-list-group>
            <!-- accepted products -->
            <b-list-group-item v-for="item in cart.items" v-if="!item.wait_listed" class="d-flex justify-content-between align-items-center">
              {{itemFormat(item)}}<div v-if="item.price">£{{item.price.toFixed(2)}}</div>
            </b-list-group-item>

            <!-- wait-listed items -->
            <b-list-group-item v-for="item in cart.items" v-if="item.wait_listed" class="d-flex justify-content-between align-items-center" variant="warning">
              {{itemFormat(item)}} <b-badge pill variant="warning">Waiting List</b-badge>
              <div v-if="item.price">£{{item.price.toFixed(2)}}</div>
            </b-list-group-item>

            <!-- transaction fee -->
            <b-list-group-item class="d-flex justify-content-between align-items-center small font-italic font-weight-light">
              Transaction fee <div>£{{cart.transaction_fee.toFixed(2)}}</div>
            </b-list-group-item>

            <!-- TOTAL -->
            <b-list-group-item variant="primary" class="d-flex justify-content-between align-items-center font-weight-bold">
              Total <div>£{{(cart.transaction_fee + cart.total).toFixed(2)}}</div>
            </b-list-group-item>

            <!-- TOTALs now and later -->
            <b-list-group-item v-if="(pay_all != 'y') && has_waiting" variant="primary" class="d-flex justify-content-between align-items-center">
              Amount due now <div>£{{cart.pay_now_total.toFixed(2)}}</div>
            </b-list-group-item>
            <b-list-group-item v-if="(pay_all != 'y') && has_waiting" variant="primary" class="d-flex justify-content-between align-items-center">
              Amount due later <div>£{{(cart.transaction_fee + cart.total - cart.pay_now_total).toFixed(2)}}</div>
            </b-list-group-item>

          </b-list-group>
          <b-alert show  v-if="has_waiting" variant="warning" class="mb-4 my-4">
            <p><font-awesome icon="exclamation-triangle"/> Some of the items are on the waiting list. You have the following options:</p>
            <b-form-group label="">
              <b-form-radio-group v-model="pay_all" @input="requestCheckout" stacked>
                <b-form-radio value="y">Pay 100% in advance now (can be refunded on request)</b-form-radio>
                <b-form-radio value="">Let us process payment automatically when the place is available</b-form-radio>
              </b-form-radio-group>
            </b-form-group>
          </b-alert>
          <button class="btn btn-success my-4" @click="hideModal();stripeCheckout()" v-if="cart.checkout_enabled">
            <font-awesome icon="credit-card"/> Sign up and pay
          </button>
      </div>
    </b-modal>

    <b-modal  size="lg" id="paymentErrorModal" ref="paymentErrorModal" hide-footer
              title="Payment Error"
              header-bg-variant="danger"
              header-text-variant="light"
              body-bg-variant="danger"
              body-text-variant='light'>
      <div class="d-block">
        An error has occured during processing your payment. The money haven't been transfered.<br/>
        {{payment_response.error_message}}
      </div>
    </b-modal>

  </div>
</template>

<script>
import { mapState, mapActions,mapGetters } from 'vuex'
import { sync } from 'vuex-pathify';
import FontAwesome from './FontAwesome.vue'

export default {
  components: {FontAwesome},
  computed: {
    ...mapState(['cart', 'errors', 'payment_response']),
    has_waiting: function() {
      return this.cart.items.filter((i) => i.wait_listed).length > 0
    },
    ...sync({
      pay_all:'registration@pay_all',
    }),
  },
  methods: {
    itemFormat(item) {
      let values = [item.name]
      if (item.person) {values.push(item.person)}
      if (item.dance_role) {values.push(item.dance_role)}
      return values.join(' / ')
    },
    hideModal() {
      this.$refs.checkoutModal.hide()
    },
    ...mapActions(['requestPrice', 'requestCheckout', 'stripeCheckout'])
  },
  watch: {
    payment_response: function() {
      if (!this.payment_response.success) {
        this.$refs.paymentErrorModal.show()
      } else if (this.payment_response.pmt_token) {
        window.location = '/order/' + this.payment_response.pmt_token
      }
    },
  }
}
</script>
