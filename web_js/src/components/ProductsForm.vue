<template>
  <div id="registration_form">
    <div class="container-fluid">
      <!-- {{getPricingSubmitData}} -->
        <div class="container my-4" v-for="(dayWorkshops, day) in layout['workshops']">
            <h3 >Workshops: {{day}}</h3>
            <table class="table">
                <tbody>
                <tr v-for="row in dayWorkshops">
                    <td v-for="(productKey, level) in row" style="border:none">
                      <workshop-card :inputName="productKey">
                        {{getProductByKey(productKey).info}}
                      </workshop-card>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
  </div>
</template>

<script>
import WorkshopCard from './WorkshopCard.vue';
import LocationInput from './LocationInput.vue';
import { mapState, mapActions,mapGetters } from 'vuex'

export default {
  components: {
    WorkshopCard,
    LocationInput,
  },
  created() {
      this.$store.dispatch('initEvent');
    },
  props:{
  },
  data: function () {
    return {
    }
  },
  computed: {
    ...mapState(['products', 'layout']),
    ...mapGetters(['getSelectedProducts', 'getProductByKey', 'getPricingSubmitData']),
  },
  watch: {
    getSelectedProducts: function() {
      this.$store.dispatch('requestPrice');
    }
  },
  methods: {
  },
}
</script>
