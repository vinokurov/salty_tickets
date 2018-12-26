<template>
  <div id="registration_form">
    <div class="container-fluid">
      <div class="container my-4">
        <h2 class="h2 display-4 text-center my-5">Weekend Passes</h2>
        <table class="table" v-if="tickets.length">
          <tbody>
            <tr>
              <td style="border:none">
                <PassTicketCard
                  inputName='full_pass'
                  :special_price="getSpecialPrice('full_pass')"
                />
              </td>
              <td style="border:none">
                <PassTicketCard
                  inputName='party_pass'
                  :special_price="getSpecialPrice('party_pass')"
                />
              </td>
            </tr>
            <tr>
              <td style="border:none">
                <PassTicketWithRoleCard
                  inputName='shag_novice'
                  :special_price="getSpecialPrice('shag_novice')"
                />
              </td>
              <td style="border:none">
                <PassTicketWithRoleCard
                  inputName='shag_novice_no_parties'
                  :special_price="getSpecialPrice('shag_novice_no_parties')"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="container-fluid">
      <!-- {{getPricingSubmitData}} -->
      <div class="container my-4">
        <h2 class="h2 display-4 text-center my-5">Workshops</h2>
      </div>
        <div class="container mt-4 mb-5" v-for="(dayWorkshops, day) in layout['workshops']">
            <h3 class="d-block p-2 bg-dark text-white" >{{day}}</h3>
            <table class="table">
              <!-- <thead>
                <th v-for="(productKey, level) in dayWorkshops[0]" style="border:none">
                  <b-card :header="level" class="text-center" no-body bg-variant="dark" text-variant='light'/>
                </th>
              </thead> -->
                <tbody>
                <tr v-for="row in dayWorkshops">
                    <td v-for="(productKey, level) in row" style="border:none">
                      <workshop-card
                        :inputName="productKey"
                        :headerColor="level_color_codes[getTicketByKey(productKey).level]"
                        v-if="productKey"
                        :special_price="getSpecialPrice(productKey)"
                        />
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>


    <div class="container-fluid">
      <div class="container my-4">
        <h2  class="h2 display-4 text-center my-5">Parties</h2>

        <table class="table" v-if="tickets.length">
          <tbody>
            <tr>
              <td style="border:none">
                <PartyTicketCard inputName='friday_party' :special_price="getSpecialPrice('friday_party')"/>
              </td>
              <td style="border:none">
                <PartyTicketCard inputName='saturday_party' :special_price="getSpecialPrice('saturday_party')"/>
              </td>
              <td style="border:none">
                <PartyTicketCard inputName='sunday_party' :special_price="getSpecialPrice('saturday_party')"/>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="container-fluid">
      <div class="container my-4" v-if="products.length">
        <h2  class="h2 display-4 text-center my-5">Extras</h2>

        <b-container>
          <b-row class="justify-content-md-center">
            <b-col col lg="8" class="text-justify">
              At Mind the Shag we are trying to make the world a better place.
              Not only by bringing more joy to the dance comunity, but also by
              keeping high environment safe and sustainable production standards.
            </b-col>
          </b-row>
          <b-row class="justify-content-md-center my-3">
            <b-col col lg="4" class="text-justify">
              Our Earth is dying and we have to realise that there is not a plan B.
              We will make our festival <b>PLASTIC FREE</b>!
              While of course we will have water,
              there will be no single use plastic cups neither at the workshops nor at the parties.
              <b>Please bring your own water bottles</b> and refill them at the festival
              or <b>get an MTS branded aluminium bottle</b>.
            </b-col>

            <b-col col lg="4" class="text-justify">
              For our T-shirts and bags we will collaborate with a <b>RESPONSIBLE SUPPLIER</b>
              to  ensure that NO CHILD LABOUR or SWEATSHOPS have been used
              in the production of our products as cheap products come from reducing the salary
              of the workers.
            </b-col>
          </b-row>
          <b-row class="justify-content-md-center">
            <b-col col lg="8" class="text-justify">
              The prices of the T-shirts, bags and aluminium bottles are very close to the costs.
              In order to keep them as low as possible they will be available on pre-order only.
              We are happy to share the transparency of the pricecost with you.
            </b-col>
          </b-row>
        </b-container>

        <div class="my-5">
          <b-card-group deck>
            <MerchandiseProductCard :inputName='products[0].key'></MerchandiseProductCard>
            <MerchandiseProductCard :inputName='products[1].key'></MerchandiseProductCard>
            <MerchandiseProductCard :inputName='products[2].key'></MerchandiseProductCard>
            <MerchandiseProductCard :inputName='products[3].key'></MerchandiseProductCard>
          </b-card-group>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import WorkshopCard from './WorkshopCard.vue';
import MerchandiseProductCard from './MerchandiseProductCard.vue';
import PassTicketCard from './PassTicketCard.vue';
import PassTicketWithRoleCard from './PassTicketWithRoleCard.vue';
import PartyTicketCard from './PartyTicketCard.vue';
import LocationInput from './LocationInput.vue';
import { mapState, mapActions,mapGetters } from 'vuex'

export default {
  components: {
    WorkshopCard,
    PassTicketCard,PassTicketWithRoleCard,
    MerchandiseProductCard,
    PartyTicketCard,
    LocationInput,
  },
  created() {
      this.$store.dispatch('initEvent');
    },
  props:{
  },
  data: function () {
    return {
      level_color_codes: {
        'St.Louis Shag': '#1E8449',
        'St.Louis Shag Novice': '#1E8449',
        'Collegiate Shag': '#1B4F72',
        'Collegiate Shag Novice': '#5499C7',
        'Collegiate Shag Veteran': '#922B21'
      },
      selected_workshops_by_category: {},
      extra_station_price: 25,
    }
  },
  computed: {
    has_full_pass: function(){
      return this.getSelectedTickets.filter((t) => t.key=='full_pass').length > 0
    },
    selected_stations_count: function() {
      return this.getSelectedTickets.filter((t) => this.getTicketByKey(t.key).level).length
    },
    station_discounted_price: function(){
      if(this.getSelectedTickets.filter((t) => t.key=='full_pass').length > 0) {
        if(this.selected_stations_count < 3) {
          return 0
        } else {
          return this.extra_station_price;
        }
      } else if (this.getSelectedTickets.filter((t) => (t.key.indexOf('shag_novice') > -1)).length > 0) {
          return this.extra_station_price
      }
    },
    clinic_discounted_price: function() {
      if(this.station_discounted_price == 0) return 15
    },
    ...mapState(['tickets', 'products', 'layout', 'prior_registrations']),
    ...mapGetters(['getSelectedTickets', 'getTicketByKey',
                  'getSelectedProducts', 'getProductByKey',
                  'getPricingSubmitData','getTicketNewPrice']),
  },
  watch: {
    getSelectedTickets: function() {
      this.$store.dispatch('requestPrice');
      this.removeOverlapping();
      this.applyPassesAutoselect()
    },
    prior_registrations: function() {
      this.disablePrior()
    }
  },
  methods: {
    disablePrior: function() {
      let keys_to_disable = []
      this.prior_registrations.registrations.forEach((reg) => {
        keys_to_disable.push(reg.ticket_key)
        this.tickets.forEach((t) => {
          if(t.start_datetime && (t.start_datetime == this.getTicketByKey(reg.ticket_key).start_datetime)) {
            keys_to_disable.push(t.key)
          }
        })
      })
      if(keys_to_disable.indexOf('shag_abc') > -1 || keys_to_disable.indexOf('shag_essentials') > -1) {
        keys_to_disable.push('shag_novice')
        keys_to_disable.push('shag_novice_no_parties')
      }

      if (keys_to_disable.indexOf('full_pass') > -1) {
        keys_to_disable.push('party_pass')
        keys_to_disable.push('shag_novice')
        keys_to_disable.push('shag_novice_no_parties')
      }
      if (keys_to_disable.indexOf('party_pass') > -1) {
        keys_to_disable.push('shag_novice')
      }
      if (keys_to_disable.indexOf('shag_novice') > -1) {
        keys_to_disable.push('party_pass')
        keys_to_disable.push('shag_novice_no_parties')
      }

      this.tickets.forEach((t) => {
        if (keys_to_disable.indexOf(t.key) > -1 ) {
          t.choice = null
          t.editable = false
        } else if (! (t.choice && t.etitable)) {
          t.editable = true
        }
      })

      this.$store.dispatch('requestPrice');

    },
    removeOverlapping: function() {
      var new_mapping = {}

      for (var i=0; i<this.getSelectedTickets.length; i++){
        var ticket_key = this.getSelectedTickets[i].key
        var category = this.getTicketByKey(ticket_key).start_datetime
        if(!category){
          category = 'pass'
        }
        new_mapping[category] = ticket_key
        if(category in this.selected_workshops_by_category)
        {
          var ticket_key_old = this.selected_workshops_by_category[category]
          if (ticket_key_old != ticket_key) {
            this.getTicketByKey(ticket_key_old).choice=null;
          }
        }
      }
      this.selected_workshops_by_category = new_mapping
    },
    applyPassesAutoselect: function() {
      var pass_key = this.selected_workshops_by_category['pass']
      var parties = ['friday_party', 'saturday_party', 'sunday_party']
      var novice_stations = ['shag_abc', 'shag_essentials']
      if (pass_key){
        var pass = this.getTicketByKey(pass_key)

        if(['full_pass', 'shag_novice', 'party_pass'].indexOf(pass_key)>-1){
          for(var i=0;i< parties.length; i++){
            var party = this.getTicketByKey(parties[i])
            party.choice = pass.choice;
            party.editable = false;
          }
        } else {
          for(var i=0;i< parties.length; i++){
            var party = this.getTicketByKey(parties[i])
            party.editable = true;
          }
        }

        if(['shag_novice', 'shag_novice_no_parties'].indexOf(pass_key)>-1) {
          for(var i=0;i< novice_stations.length; i++){
            var station = this.getTicketByKey(novice_stations[i])
            if(!(station.choice == null && station.editable == false)){
              station.choice = pass.choice;
              station.editable = false;
            }
          }
        } else {
          for(var i=0;i< novice_stations.length; i++){
            var station = this.getTicketByKey(novice_stations[i])
            if(!(station.choice == null && station.editable == false)){
              station.editable = true;
            }
          }
        }

      } else {
        for(var i=0;i< parties.length; i++){
          var party = this.getTicketByKey(parties[i])
          party.editable = true;
        }
        for(var i=0;i< novice_stations.length; i++){
          var station = this.getTicketByKey(novice_stations[i])
          station.editable = true;
        }
      }

    },
    getSpecialPrice(ticket_key){
      let new_price = this.getTicketNewPrice(ticket_key)
      let base_price = this.getTicketByKey(ticket_key).price
      if ((new_price != null) && (new_price < base_price)) return new_price
    },
  },
}
</script>
