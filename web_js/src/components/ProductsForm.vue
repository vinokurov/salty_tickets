<template>
  <div id="registration_form">

    <div class="container-fluid">
      <div class="container my-4">
        <h2 class="h2 display-4 text-center my-5">Weekend Passes</h2>
        <table class="table" v-if="tickets.length">
          <tbody>
            <tr>
              <td style="border:none">
                <PassTicketCard inputName='full_pass'>
                  {{getTicketByKey('full_pass').info}}
                </PassTicketCard>
              </td>
              <td style="border:none">
                <PassTicketCard inputName='party_pass'>
                  {{getTicketByKey('party_pass').info}}
                </PassTicketCard>
              </td>
            </tr>
            <tr>
              <td style="border:none">
                <PassTicketWithRoleCard inputName='shag_novice'>
                  {{getTicketByKey('shag_novice').info}}
                </PassTicketWithRoleCard>
              </td>
              <td style="border:none">
                <PassTicketWithRoleCard inputName='shag_novice_no_parties'>
                  {{getTicketByKey('shag_novice_no_parties').info}}
                </PassTicketWithRoleCard>
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
                <PartyTicketCard inputName='friday_party'/>
              </td>
              <td style="border:none">
                <PartyTicketCard inputName='saturday_party'/>
              </td>
              <td style="border:none">
                <PartyTicketCard inputName='sunday_party'/>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="container-fluid">
      <div class="container my-4" v-if="products.length">
        <h2  class="h2 display-4 text-center my-5">Extras</h2>

        <div>
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
    ...mapState(['tickets', 'products', 'layout']),
    ...mapGetters(['getSelectedTickets', 'getTicketByKey',
                  'getSelectedProducts', 'getProductByKey',
                  'getPricingSubmitData']),
  },
  watch: {
    getSelectedTickets: function() {
      this.$store.dispatch('requestPrice');
      this.removeOverlapping();
      this.applyPassesAutoselect()
    },
  },
  methods: {
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
            station.choice = pass.choice;
            station.editable = false;
          }
        } else {
          for(var i=0;i< novice_stations.length; i++){
            var station = this.getTicketByKey(novice_stations[i])
            station.editable = true;
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
      if(ticket_key == 'shag_clinic'){
        return this.clinic_discounted_price
      } else {
        return this.station_discounted_price
      }
    },
  },
}
</script>
