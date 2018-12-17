<template>
  <div id="app">

     <div class="container-fluid">
         <div class="container">


            <b-card no-body bg-variant="light" class="mb-4">
              <h4 slot="header">{{event_info.name}}</h4>
              <b-card>
                <dl>
                  <dd><strong>Count:</strong> {{event_info.summary.persons_count}}</dd>
                  <dd><strong>Workshops Accepted:</strong> {{event_info.summary.workshops_accepted}}</dd>
                  <dd><strong>Workshops Wait Listed:</strong> {{event_info.summary.workshops_wait_listed}}</dd>
                  <dd><strong>Total Sales:</strong> £{{event_info.summary.total_sales}}</dd>
                  <dd><strong>Amount Paid:</strong> £{{event_info.summary.amount_paid}}</dd>
                  <dd><strong>Amount Due Later:</strong> £{{event_info.summary.amount_due_later}}</dd>
                </dl>
              </b-card>
           </b-card>


          <h3>Workshops</h3>
            <b-card no-body bg-variant="light" class="mb-4">
              <b-table striped hover small :items="event_info.products"
                       :fields="['title', 'start_datetime', 'available', 'leaders', 'followers', 'current_ratio', 'has_wait_list', 'actions']">
                <template slot="actions" slot-scope="row">
                  <a><b-badge @click.stop="row.toggleDetails">
                   {{ row.detailsShowing ? 'Hide' : 'Show' }} Registrations
                 </b-badge></a>
                </template>
                <template slot="row-details" slot-scope="row">
                 <b-card>
                   <b-table striped hover small :items="row.item.registrations"
                            :fields="['name', 'price', 'paid_price', 'dance_role', 'partner', 'wait_listed', 'active']">
                          </b-table>
                 </b-card>
               </template>
             </b-table>
           </b-card>

         <br/>
         <b-btn v-b-toggle.payments_collapse variant="primary">Payments</b-btn>
         <b-collapse id="payments_collapse" class="mt-2">
           <b-card no-body bg-variant="light" class="mb-4">
             <b-table striped hover small :items="event_info.payments"
                      :fields="['name', 'partner', 'price', 'paid_price', 'status', 'actions']">
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
