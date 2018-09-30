<template>
  <div id="app">
    <checkout-header/>
    <registration-form/>
    <products-form/>
  </div>
</template>

<script>
import ProductsForm from '../../components/ProductsForm.vue';
import CheckoutHeader from '../../components/CheckoutHeader.vue';
import RegistrationForm from '../../components/RegistrationForm.vue';

export default {
  name: 'app',
  components: {
    ProductsForm,
    CheckoutHeader,
    RegistrationForm,
  },
  methods: {
  },
};
</script>
