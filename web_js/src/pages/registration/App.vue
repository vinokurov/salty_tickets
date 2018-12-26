<template>
  <div id="app">
    <checkout-header/>
    <registration-jumbotron/>
    <prices-section/>
    <registration-form/>
    <products-form/>
  </div>
</template>

<script>
import PricesSection from '../../components/PricesSection.vue';
import ProductsForm from '../../components/ProductsForm.vue';
import CheckoutHeader from '../../components/CheckoutHeader.vue';
import RegistrationForm from '../../components/RegistrationForm.vue';
import RegistrationJumbotron from '../../components/RegistrationJumbotron.vue';

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
};
</script>

<style lang="scss">
@import '../../../style/custom-bootstrap.scss';
@import '../../../node_modules/bootstrap/scss/bootstrap.scss';
</style>
