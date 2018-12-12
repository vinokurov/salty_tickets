<template>
  <div id="registration_form">

    <div class="container-fluid">
      <div class="container my-4">
        <PassTicketCard :inputName='ticket.key' v-for="ticket in tickets" v-if="ticket.tags.indexOf('pass')>=0">
          {{getTicketByKey(ticket.key).info}}
        </PassTicketCard>
      </div>
    </div>

    <div class="container-fluid">
      <!-- {{getPricingSubmitData}} -->
        <div class="container my-4" v-for="(dayWorkshops, day) in layout['workshops']">
            <h3 >{{day}}</h3>
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
                        v-if="productKey">
                        {{getTicketByKey(productKey).info}}
                        <!-- {{productKey}} -->
                      </workshop-card>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>


    <div class="container-fluid">
      <div class="container my-4">
        <div>
          <b-card-group deck>
          <MerchandiseProductCard :inputName='product.key' v-for="product in products">
            <!-- {{getProductByKey(product.key).title}} -->
          </MerchandiseProductCard>
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
import LocationInput from './LocationInput.vue';
import { mapState, mapActions,mapGetters } from 'vuex'

export default {
  components: {
    WorkshopCard,
    PassTicketCard,
    MerchandiseProductCard,
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
        'Collegiate Shag': '#1B4F72',
        'Collegiate Shag Novice': '#5499C7',
        'Collegiate Shag Veteran': '#922B21'
      }
    }
  },
  computed: {
    ...mapState(['tickets', 'products', 'layout']),
    ...mapGetters(['getSelectedTickets', 'getTicketByKey',
                  'getSelectedProducts', 'getProductByKey',
                  'getPricingSubmitData']),
  },
  watch: {
    getSelectedTickets: function() {
      this.$store.dispatch('requestPrice');
    }
  },
  methods: {
  },
}
</script>
