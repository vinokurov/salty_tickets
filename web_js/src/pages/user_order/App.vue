<template>
  <div id="app">

     <div class="container-fluid">
         <div class="container">


            <b-card no-body>
              <h4 slot="header">Registration Details</h4>
              <table class="table">
                <tbody>
                  <tr><th scope="row">Name</th><td>{{user_order_info.name}}</td></tr>
                  <tr><th scope="row">Email</th><td>{{user_order_info.email}}</td></tr>
                  <tr><th scope="row">Token</th><td>{{user_order_info.ptn_token}}</td></tr>
                </tbody>
              </table>
           </b-card>

          <h2>Registrations</h2>
          <b-card no-body v-for="product in user_order_info.products">
            <h4 slot="header">{{product.title}} / {{product.person}}</h4>
            <b-card-body>
              <p class="card-text">{{product.info}}</p>
            </b-card-body>
            <table class="table">
              <tbody>
                <tr><th scope="row">Start</th><td>{{product.start_datetime}}</td></tr>
                <tr><th scope="row">End</th><td>{{product.end_datetime}}</td></tr>
                <tr><th scope="row">Teachers</th><td>{{product.teachers}}</td></tr>
                <tr><th scope="row">Level</th><td>{{product.level}}</td></tr>
                <tr><th scope="row">Your partner</th><td>{{product.partner}}</td></tr>
              </tbody>
            </table>
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
