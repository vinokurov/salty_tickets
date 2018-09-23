<template>
   <div class="container-fluid">
       <div class="container">
           <div class="card bg-light">
               <div class="card-body">
                   <h2> Your details</h2>
                   <form id="registration">
                   <b-input-group class="my-2">
                        <b-input-group-text><font-awesome icon="user"></font-awesome></b-input-group-text>
                        <b-form-input v-model="primaryName" class="form-control" placeholder="Your name" id="name" name="name"></b-form-input>
                   </b-input-group>
                   <b-input-group class="my-2">
                        <b-input-group-text><font-awesome icon="envelope"/></b-input-group-text>
                        <b-form-input v-model="primaryEmail" class="form-control" placeholder="Your email" id="email" name="email"></b-form-input>
                   </b-input-group>
                   <location-input v-on:input="primaryLocation = $event" name="location"/>
                   <b-form-select  v-if="partnerRequired" v-model="primaryDanceRole" :options="dance_role_options" class="mb-3" />

                   <div v-if="partnerRequired">
                       <h2> Your partner details</h2>
                       <small>(*If you are buying tickets for yourself and for your partner)</small>
                       <b-input-group class="my-2">
                            <b-input-group-text><font-awesome icon="user"/></b-input-group-text>
                            <b-form-input v-model.lazy="partnerName" class="form-control" placeholder="Your partner name"></b-form-input>
                       </b-input-group>
                       <b-input-group class="my-2">
                            <b-input-group-text><font-awesome icon="envelope"/></b-input-group-text>
                            <b-form-input v-model.lazy="partnerEmail" class="form-control" placeholder="Your partner email"></b-form-input>
                       </b-input-group>
                       <location-input v-model.lazy="partnerLocation" name="partner_location"/>
                   </div>
                    <hr>
                   <textarea v-model="primaryComments" class="form-control" id="comment"
                                  name="comment" placeholder="Any comments"></textarea>
                  </form>

               </div>
           </div>
       </div>
   </div>
</template>

<script>
import { mapState, mapActions,mapGetters } from 'vuex'
import { sync } from 'vuex-pathify';
import FontAwesome from './FontAwesome.vue'
import LocationInput from './LocationInput.vue'

export default {
  components: {FontAwesome, LocationInput},
  data: function() {
    return {
      dance_role_options: [
        {value: null, text: "Your dance role"},
        {value: 'leader', text: 'Leader'},
        {value: 'follower', text: 'Follower'},
      ],
    }
  },
  computed: {
    // ...sync(['registration']),
    ...sync({
      primaryName:'registration@primary.name',
      primaryEmail:'registration@primary.email',
      primaryLocation: 'registration@primary.location',
      primaryComments: 'registration@primary.comments',
      primaryDanceRole: 'registration@primary.dance_role',
      partnerName: 'registration@partner.name',
      partnerEmail: 'registration@partner.email',
      partnerLocation: 'registration@partner.location'
    }),
    ...mapGetters(['partnerRequired']),
  },
  watch: {
    registration () {
      console.log(this.registration)
      this.$state.commit('SET_REGISTRATION', this.registration)
    }
  }
}
</script>
