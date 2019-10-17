<template>
   <div class="container-fluid">
       <div class="container">
           <div class="card bg-light">
               <div class="card-body">
                 <span v-if="!priorPrimaryName">
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
                 </form>
               </span>
               <span v-if="!priorPartnerName">
                   <b-form-select  v-if="partnerRequired" v-model="primaryDanceRole" :options="dance_role_options" class="mb-3" style="background-image: none"/>

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
                 </span>
                 <span v-if="!priorPrimaryName">
                    <hr>
                   <textarea v-model="primaryComment" class="form-control" id="comment"
                                  name="comment" placeholder="Any comments"></textarea>
                    <b-input-group class="my-2">
                         <b-input-group-text><font-awesome icon="key"></font-awesome></b-input-group-text>
                         <b-form-input v-model="primaryDiscountCode" class="form-control" placeholder="Discount/Group code" id="discount_code" name="discount_code"></b-form-input>
                         <b-btn @click="primaryDiscountCode=''" v-if="primaryDiscountCode"><font-awesome icon="times"/></b-btn>
                    </b-input-group>
                    <b-button-group>
                      <b-button @click="primaryDiscountCode='OVERSEAS'">
                        Apply an overseas discount
                      </b-button >
                      <b-btn id="overseas-info"><font-awesome icon="info-circle" class="close"/></b-btn>
                    </b-button-group>
                    <b-popover target="overseas-info" triggers="click blur">
                      For those who travel to Mind the Shag from another continent or require a visa to enter the UK.
                    </b-popover>
                    <!-- <b-button @click="primaryDiscountCode='OVERSEAS'">
                      Create New Group
                    </b-button > -->
                  </span>

                    <h3 class="h3 my-4">Already registered?</h3>
                    <b-input-group class="my-2">
                         <b-input-group-text><font-awesome icon="key"></font-awesome></b-input-group-text>
                         <b-form-input v-model="registrationToken" class="form-control" placeholder="Prior Registration Token" id="registration_token" name="registration_token"></b-form-input>
                         <b-btn @click="registrationToken=''" v-if="registrationToken"><font-awesome icon="times"/></b-btn>
                    </b-input-group>

                    <div v-if="priorPrimaryName">
                      <p><font-awesome icon="user"/> {{priorPrimaryName}}</p>
                      <p v-if="priorPartnerName"><font-awesome icon="user"/> {{priorPartnerName}}</p>
                      <b-list-group>
                        <b-list-group-item v-for="ticket in getPriorTickets">
                          <font-awesome icon="ticket-alt"/> {{ticket.title}} x {{ticket.amount}}
                        </b-list-group-item>
                      </b-list-group>
                    </div>


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
      overseasDiscount: '',
    }
  },
  computed: {
    // ...sync(['registration']),
    ...sync({
      primaryName:'registration@primary.name',
      primaryEmail:'registration@primary.email',
      primaryLocation: 'registration@primary.location',
      primaryComment: 'registration@primary.comment',
      primaryDanceRole: 'registration@primary.dance_role',
      primaryDiscountCode: 'registration@primary.discount_code',
      partnerName: 'registration@partner.name',
      partnerEmail: 'registration@partner.email',
      partnerLocation: 'registration@partner.location',
      registrationToken: 'registration@registration_token',
      priorPrimaryName: 'prior_registrations@person',
      priorPartnerName: 'prior_registrations@partner',
      priorRegistrations: 'prior_registrations@registrations',
    }),
    ...mapGetters(['partnerRequired','getPriorTickets']),
  },
  watch: {
    registration () {
      this.$state.commit('SET_REGISTRATION', this.registration)
    },
    primaryDiscountCode () {
      this.$store.dispatch('requestPrice');
    },
    registrationToken() {
      this.$store.dispatch('requestPriorRegistrations');
    },
    createGroup() {
      this.$store.dispatch('postRequest', ('/prior_registrations/mind_the_shag_2020'))
    },
  }
}
</script>
