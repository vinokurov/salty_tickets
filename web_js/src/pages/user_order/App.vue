<template>
  <div id="app">

     <div class="container-fluid">
         <div class="container">


           <div class="jumbotron text-center">

             <!--Title-->
             <h1 class="card-title h2-responsive mt-2"><strong>Salty Brizzle ☆ Shag Weekend</strong></h1>
             <!--Subtitle-->
             <p class="blue-text mb-4 font-bold">17-18 November, 2018</p>
           </div>

            <b-card no-body class="mb-4"  bg-variant="light">
              <h4 slot="header">Details</h4>
              <b-card>
                <dl>
                  <dd><strong>Name:</strong> {{user_order_info.name}}</dd>
                  <dd><strong>Email:</strong> {{user_order_info.email}}</dd>
                  <dd><strong>Token:</strong> {{user_order_info.ptn_token}}</dd>
                </dl>
              </b-card>
              <b-card-footer>
                <strong>Total Price:</strong> £{{user_order_info.price}}<br>
                <strong>Total Paid:</strong> £{{user_order_info.paid_price || 0}}
              </b-card-footer>
           </b-card>

          <h2>Registrations</h2>
          <b-card no-body v-for="product in user_order_info.products" bg-variant="light" class="mb-4">
            <h4 slot="header">{{product.title}} / {{product.person}}</h4>
            <b-card-body>
              <p class="card-text">{{product.info}}</p>
              <b-badge variant="success" v-if="!product.wait_listed">ACCEPTED</b-badge>
              <b-badge variant="warning" v-if="product.wait_listed">WAITING LIST</b-badge>
            </b-card-body>
            <b-card>
              <dl>
                <dd><strong>Dance role:</strong> {{product.dance_role}}</dd>
                <dd><strong>Start:</strong> {{product.start_datetime.replace(':00', '')}}</dd>
                <dd><strong>End:</strong> {{product.end_datetime.replace(':00', '')}}</dd>
                <dd><strong>Teachers:</strong> {{product.teachers}}</dd>
                <dd><strong>Level:</strong> {{product.level}}</dd>
                <dd v-if="product.partner"><strong>Your partner:</strong> {{product.partner}}</dd>
              </dl>
            </b-card>
            <b-card-footer>Price: £{{product.price}}, Paid: £{{product.paid_price || 0}}</b-card-footer>
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
