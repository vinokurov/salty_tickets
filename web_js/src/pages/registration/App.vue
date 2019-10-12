<template>
  <div id="app">
    <checkout-header/>
    <registration-jumbotron/>
    <prices-section v-if="event_active"/>
    <registration-form v-if="event_active"/>
    <products-form v-if="event_active"/>

    <b-container fluid v-if="!event_active">
      <b-container class="my-4">
        <h3>Online registration is closed</h3>
      </b-container>
    </b-container>

  </div>
</template>

<script>
import PricesSection from '../../components/PricesSection.vue';
import ProductsForm from '../../components/ProductsForm.vue';
import CheckoutHeader from '../../components/CheckoutHeader.vue';
import RegistrationForm from '../../components/RegistrationForm.vue';
import RegistrationJumbotron from '../../components/RegistrationJumbotron.vue';
import { mapState, mapActions,mapGetters } from 'vuex'

export default {
  name: 'app',
  components: {
    PricesSection,
    ProductsForm,
    CheckoutHeader,
    RegistrationForm,
    RegistrationJumbotron,
  },
  methods: {
  },
  computed: {
  ...mapState(['event_active']),
  },
};
</script>

<style lang="scss">
@import '../../../style/custom-bootstrap.scss';
@import '../../../node_modules/bootstrap/scss/bootstrap.scss';
</style>
