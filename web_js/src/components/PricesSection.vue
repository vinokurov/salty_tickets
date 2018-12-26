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
            <thead>
              <th class="table-secondary">
                Super Off Peak<br/><small> First 150 stations</small><br/>
                <b-badge pill variant="danger">SOLD OUT</b-badge>
              </th>
              <th class="table-success">
                Off Peak<br/><small>150-500 stations</small><br/>
                <b-badge pill variant="success">CURRENT TARIFF</b-badge>
              </th>
              <th>Rush Hour<br/><small>After 500 stations</small></th>
            </thead>
            <tbody>
              <tr>
                <td>
                  <b-list-group>
                    <b-list-group-item variant="secondary">
                      <small>Full Pass</small><br/>£120
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Party Pass</small><br/>£50
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Single/extra station</small><br/>£30 / £25
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Shag Clinic</small><br/>£40
                    </b-list-group-item>
                    <b-list-group-item variant="secondary">
                      <small>Shag novice track</small><br/>£90 / £40
                    </b-list-group-item>
                  </b-list-group>
                </td>
                <td>
                  <b-list-group>
                    <b-list-group-item variant="success">
                      <small>Full Pass</small><br/>£140
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Party Pass</small><br/>£50
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Single/extra station</small><br/>£35 / £25
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Shag Clinic</small><br/>£40
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Shag novice track</small><br/>£105 / £55
                    </b-list-group-item>
                    <b-list-group-item variant="success">
                      <small>Single parties</small><br/>£20 /£25/ £15
                    </b-list-group-item>
                  </b-list-group>
                </td>
                <td>
                  <b-list-group>
                    <b-list-group-item>
                      <small>Full Pass</small><br/>£150
                    </b-list-group-item>
                    <b-list-group-item>
                      <small>Party Pass</small><br/>£55
                    </b-list-group-item>
                    <b-list-group-item>
                      <small>Single/extra station</small><br/>£35 / £30
                    </b-list-group-item>
                    <b-list-group-item>
                      <small>Shag Clinic</small><br/>£40
                    </b-list-group-item>
                    <b-list-group-item>
                      <small>Shag novice track</small><br/>£110 / £60
                    </b-list-group-item>
                    <b-list-group-item>
                      <small>Single parties</small><br/>£20 /£25/ £15
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
                <h2>£20</h2>
                <small>Off full pass/shag novice ticket</small><br/><br/>
                <b>Overseas discount</b> for people travelling from outside
                European continent or those who require visa for the UK.
              </b-col>
              <b-col col lg="4">
                <h2>£10</h2>
                <small>Off full pass/shag novice ticket</small><br/><br/>
                <b>Discount for groups</b> of at least 5 dancers coming from
                the same country and outside London.
              </b-col>
            </b-row>
          </b-container>
        </div>
      </div>

    </div>
</template>

<script>
import { mapState, mapActions,mapGetters } from 'vuex'
import { sync } from 'vuex-pathify';
export default {
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
