<template>
  <button @click="fetchResults" />
</template>

<script>
  import axios from 'axios'

  export default {
    data () {
      return {
        value: null,
        state: null,
      }
    },

    methods: {
      async fetchResults () {
        const response = await axios.get('mock/service')
        console.log('RECEIVED: ' + response.data )
        this.value = response.data
      }
    },
    watch: {
      state: function () {
        this.fetchResults()
      }
    }
  }
</script>
