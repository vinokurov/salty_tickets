<template>
    <b-form-group
      :invalid-feedback="messageError"
      :valid-feedback="messageSuccess"
      :state="state"
    >
        <b-input-group>
            <b-input-group-text>
              <font-awesome icon="map-marker"/>
            </b-input-group-text>
            <b-form-input placeholder="Location (country, state, city, etc.)" v-model="queryText"></b-form-input>
        </b-input-group>
    </b-form-group>
</template>

<script>
import axios from 'axios'
import FontAwesome from './FontAwesome.vue'
import BootstrapVue from 'bootstrap-vue'


export default{
  name: 'LocationInput',
  components: {FontAwesome, BootstrapVue},

  props: {
    'name': String,
  },
  data: function () {
    return {
      queryText: null,
      lastQuery: null,
      location: null,
      messageError: null,
      messageSuccess: null,
      locationText: null,
      queryResponse: null,
    }
  },
  methods: {
    async callLocationService () {
      if (this.queryText != this.lastQuery) {
        const url = 'https://nominatim.openstreetmap.org/search/' + encodeURI(this.queryText) + '?format=json&addressdetails=1&limit=1&accept-language=en'
        const response = await axios.get(url)
        this.queryResponse = response
        this.lastQuery = this.queryText
      }
    },
    locationShortName(locationJSON) {
      try {
        const locationType = locationJSON['type']
        const address = locationJSON['address']
        let locationList = [address['country']]
        if (address['country'] != address['state']) {
          locationList.push(address['state'])
        }
        if (locationType in address) {
          locationList.push(address[locationType])
        } else if ('county' in address) {
          locationList.push(address['county'])
        }
        return locationList.join(', ')
      } catch(err) {
        return locationJSON['display_name']
      }
    }
  },
  watch: {
    location: function() {
      let value = this.location
      if (value) {
        value['query'] = this.queryText
        this.$emit('input', value);
        this.$emit('change', value)
      } else {
        this.$emit('input', '');
        this.$emit('change', '')
      }

    },
    queryText: function() {
      if (this.queryText) {
        if (this.queryText != this.lastQuery) {
          setTimeout(function () { this.callLocationService() }.bind(this), 2000)
        }
      }
    },
    queryResponse: function () {
      if (this.queryResponse) {
        if (this.queryResponse.status == 200) {
          if (this.queryResponse.data.length > 0) {
            const locData = this.queryResponse.data[0]
            this.locationText = this.locationShortName(locData)
            this.location = locData['address'];
            this.messageSuccess = this.locationText
            this.messageError = ''
            return
          } else {
            this.messageError = 'Location not found...'
          }
        } else {
          this.messageError = 'Location server is failing...'
        }
      }
      this.messageSuccess = ''
      this.locationText = ''
      this.location = null
    }
  },
  computed: {
    state: function () {
      if (this.messageError) {
        return false
      } else if (this.locationText) {
        return true
      } else return null
    },
  },
}
</script>
