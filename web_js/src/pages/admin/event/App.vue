<template>
  <div id="app">

     <div class="container-fluid">
         <div class="container">


            <b-card no-body bg-variant="light" class="mb-4">
              <h4 slot="header">Event</h4>
              <table class="table">
                <tbody>
                  <tr><th scope="row">Name</th><td>{{event_info.name}}</td></tr>
                </tbody>
              </table>
           </b-card>


          <b-btn v-b-toggle.registrations_collapse variant="primary">Registrations</b-btn>
          <b-collapse id="registrations_collapse" class="mt-2">
            <b-card no-body bg-variant="light" class="mb-4">
              <b-table striped hover :items="event_info.registrations" :fields="['name', 'product', 'price', 'paid_price', 'dance_role', 'partner', 'wait_listed', 'active', 'actions']">
                <template slot="actions" slot-scope="row">
                  <a><b-badge @click.stop="row.toggleDetails">
                   {{ row.detailsShowing ? 'Hide' : 'Show' }} Details
                 </b-badge></a>
                </template>
                <template slot="row-details" slot-scope="row">
                 <b-card>
                   <ul>
                     <li v-for="(value, key) in row.item" :key="key">{{ key }}: {{ value}}</li>
                   </ul>
                 </b-card>
               </template>
             </b-table>
           </b-card>
         </b-collapse>

         <br/>
         <b-btn v-b-toggle.payments_collapse variant="primary">Payments</b-btn>
         <b-collapse id="payments_collapse" class="mt-2">
           <b-card no-body bg-variant="light" class="mb-4">
             <b-table striped hover :items="event_info.payments" :fields="['name', 'price', 'paid_price', 'status', 'actions']">
               <template slot="actions" slot-scope="row">
                 <a><b-badge @click.stop="row.toggleDetails">
                  {{ row.detailsShowing ? 'Hide' : 'Show' }} Details
                </b-badge></a>
               </template>
               <template slot="row-details" slot-scope="row">
                <b-card>
                  <ul>
                    <li v-for="(value, key) in row.item" :key="key">{{ key }}: {{ value}}</li>
                    <li><a :href="'/order/' + row.item['pmt_token']"><b-badge>Order Info</b-badge></a></li>
                  </ul>
                </b-card>
              </template>
             </b-table>
          </b-card>
        </b-collapse>

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
    ...mapState(['event_info']),
  },
};
</script>
