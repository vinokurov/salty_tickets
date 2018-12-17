<template>
  <div id="app">

     <div class="container-fluid">
         <div class="container">
           <div class="jumbotron text-center">
             <h1 class="card-title h2-responsive mt-2"><strong>Mind the Shag ☆ London Shag Festival</strong></h1>
             <p class="blue-text mb-4 font-bold">29-31 March, 2019</p>
           </div>
         </div>
       </div>

      <div class="container-fluid">
          <div class="container">
            <b-card no-body class="mb-4 shadow "  bg-variant="light">
              <h4 slot="header">Details</h4>
              <b-card>
                <dl>
                  <dd><strong>Name:</strong> {{user_order_info.name}}</dd>
                  <dd><strong>Email:</strong> {{user_order_info.email}}</dd>
                  <!-- <dd><strong>Token:</strong> {{user_order_info.ptn_token}}</dd> -->
                </dl>
              </b-card>
              <b-card-footer>
                <strong>Total Price:</strong> £{{user_order_info.price}}<br>
                <strong>Total Paid:</strong> £{{user_order_info.paid_price || 0}}
              </b-card-footer>
           </b-card>
         </div>
       </div>

       <div class="container-fluid"  v-if="user_order_info.tickets && user_order_info.tickets.length">
         <div class="container">
          <h2 class="h2">Registrations</h2>
          <b-card no-body v-for="ticket in user_order_info.tickets" bg-variant="light" class="mb-4 shadow ">
            <h4 slot="header">{{ticket.title}} / {{ticket.person}}</h4>
            <b-card-body>
              <p class="card-text">{{ticket.info}}</p>
              <b-badge variant="success" v-if="!ticket.wait_listed">ACCEPTED</b-badge>
              <b-badge variant="warning" v-if="ticket.wait_listed">WAITING LIST</b-badge>
            </b-card-body>
            <b-card v-if="ticket.ticket_class == 'WorkshopTicket'">
              <dl>
                <dd><strong>Dance role:</strong> {{ticket.dance_role}}</dd>
                <dd><strong>Start:</strong> {{ticket.start_datetime.replace(':00', '')}}</dd>
                <dd><strong>End:</strong> {{ticket.end_datetime.replace(':00', '')}}</dd>
                <dd><strong>Teachers:</strong> {{ticket.teachers}}</dd>
                <dd><strong>Level:</strong> {{ticket.level}}</dd>
                <dd v-if="ticket.partner"><strong>Your partner:</strong> {{ticket.partner}}</dd>
              </dl>
            </b-card>
            <b-card-footer>Price: £{{ticket.price}}, Paid: {{ticket.is_paid}}</b-card-footer>
         </b-card>

         <b-card no-body v-for="discount in user_order_info.discounts" bg-variant="light" class="mb-4 shadow ">
           <h4 slot="header">{{discount.info}} / {{discount.person}}</h4>
           <b-card-footer>Price: -£{{discount.price}}</b-card-footer>
        </b-card>

       </div>
     </div>

     <div class="container-fluid"  v-if="user_order_info.products && user_order_info.products.length">
       <div class="container">
        <h2 class="h2">Extras</h2>
        <b-card no-body v-for="product in user_order_info.products" bg-variant="light" class="mb-4 shadow ">
          <h4 slot="header">{{product.title}} x {{product.amount}}</h4>
          <b-card-footer>Price: £{{product.price}}, Paid: {{product.is_paid}}</b-card-footer>
       </b-card>
        </div>
      </div>
  </div>
</template>

<script>
import { mapState, mapActions,mapGetters } from 'vuex'
export default {
  name: 'app',
  components: {},
  created() {
      this.$store.dispatch('init');
  },
  methods: {},
  computed: {
    ...mapState(['user_order_info']),
  },
};
</script>

<style lang="scss">
@import '../../../style/custom-bootstrap.scss';
@import '../../../node_modules/bootstrap/scss/bootstrap.scss';
</style>
