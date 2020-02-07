<template>
  <div id="prices_section">

      <div class="container-fluid">
        <div class="container my-4">
          <b-container >
            <b-row class="justify-content-md-center">
              <b-col col lg="1" class="border border-secondary rounded-left text-center bg-info text-light shadow">
                <small>Stations</small><br/><h2>{{workshopsCount}}</h2>
              </b-col>
              <b-col col lg="1" class="border border-secondary border-left-0 text-center bg-info text-light shadow">
                <small>People</small><br/><h2>{{personsCount}}</h2>
              </b-col>
              <b-col col lg="1" class="border border-secondary border-left-0 text-center bg-info text-light shadow">
                <small>Countries</small><br/><h2>{{countriesCount}}</h2>
              </b-col>
              <b-col col lg="1" class="border border-secondary border-left-0 text-center bg-info text-light shadow">
                <small>Locations</small><br/><h2>{{locationsCount}}</h2>
              </b-col>
              <b-col col lg="2" class="border border-secondary border-left-0 rounded-right text-center bg-info text-light shadow">
                <small>Current Tariff</small><br/><h2>Off&nbsp;Peak</h2>
              </b-col>
            </b-row>
          </b-container >
        </div>
      </div>

      <div class="container-fluid">
        <div class="container my-4">
          <h2 class="h2 display-4 text-center my-5">Prices</h2>
          <table class="table text-center">
            <!-- <thead>
              <th class="table-secondary">
                Super Off Peak<br/><small> First 150 stations</small><br/>
                <b-badge pill variant="danger">SOLD OUT</b-badge>
              </th>
              <th class="table-secondary">
                Off Peak<br/><small>150-450 stations</small><br/>
                <b-badge pill variant="danger">SOLD OUT</b-badge>
              </th>
              <th class="table-success">
                Rush Hour<br/><small>After 450 stations</small><br/>
                <b-badge pill variant="success">CURRENT TARIFF</b-badge>
              </th>
            </thead>
            <tbody> -->
            <thead>
              <th class="table-secondary">
                Super Off Peak<br/><small> First 150 stations</small><br/>
                <b-badge pill variant="danger">SOLD OUT</b-badge>
              </th>
              <th class="table-success">
                Off Peak<br/><small>150-450 stations</small><br/>
                <b-badge pill variant="success">CURRENT TARIFF</b-badge>
              </th>
              <th class="table-secondary">
                Rush Hour<br/><small>After 450 stations</small><br/>
              </th>
            </thead>
            <tbody>
              <tr>
                <td>
                  <b-list-group>
                    <b-list-group-item variant="secondary">
                      <small>Full Pass</small><br/>£150
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Party Pass</small><br/>-
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Extra station</small><br/>£25
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Shag beginners track</small><br/>£110
                    </b-list-group-item>
                  </b-list-group>
                </td>
                <td>
                  <b-list-group>
                    <b-list-group-item variant="success">
                      <small>Full Pass</small><br/>£160
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Party Pass</small><br/>£65
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Single/extra station</small><br/>£35 / £25
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Shag beginners track</small><br/>£115 / £55
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Single parties</small><br/>£25 /£30/ £20
                    </b-list-group-item>
                  </b-list-group>
                </td>
                <td>
                  <b-list-group>
                    <b-list-group-item variant="secondary">
                      <small>Full Pass</small><br/>£170
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Party Pass</small><br/>£75
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Single/extra station</small><br/>£35 / £25
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Shag novice track</small><br/>£125 / £55
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Single parties</small><br/>£25 /£35/ £20
                    </b-list-group-item>
                  </b-list-group>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>


      <div class="container-fluid">
        <div class="container my-5">
          <h2 class="h2 display-4 text-center my-5">Discounts</h2>
          <b-container class="text-center">
            <b-row class="justify-content-md-center">
              <b-col col lg="4">
                <h2>£10</h2>
                <small>Off full pass/shag beginner track</small><br/><br/>
                <b>Overseas discount</b> for people travelling from outside
                European continent (<b>Asia</b>, <b>North America</b>, 
                <b>South America</b>, <b>Australia</b>, <b>Africa</b>) 
                or those who require visa for the UK.
              </b-col>
              <b-col col lg="4">
                <h2>£10</h2>
                <small>Off full pass/shag beginner track</small><br/><br/>
                <b>Discount for groups</b> of at least 5 dancers coming from
                the same country and outside London.
              </b-col>
            </b-row>
          </b-container>
        </div>
      </div>

      <div class="container-fluid">
        <!-- <div class="container my-5 text-center">
          <b-img src="/static/MTS20_XMAS.jpg" fluid alt="Fluid image"></b-img>
        </div> -->

        <!-- <div class="container my-5">
          <b-alert show variant="info">
            <h3> <font-awesome icon="info-circle" /> Hint! </h3>
            The new station <b>Solo Shag</b> is £10 cheaper if booked
            with the Full Pass or a Shag Novice ticket.
          </b-alert>
        </div> -->
      </div>

    </div>
</template>

<script>
import FontAwesome from './FontAwesome.vue'
import { mapState, mapActions,mapGetters } from 'vuex'
import { sync } from 'vuex-pathify';
export default {
  components: {FontAwesome},
  computed: {
    ...sync({
      personsCount: 'event_registration_stats@persons_count',
      workshopsCount: 'event_registration_stats@workshops_accepted',
      countriesCount: 'event_registration_stats@countries_count',
      locationsCount: 'event_registration_stats@locations_count',
    })
  }
}
</script>
