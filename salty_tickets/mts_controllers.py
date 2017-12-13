from salty_tickets.products import WORKSHOP_OPTIONS, FESTIVAL_TICKET


class MtsSignupFormController:
    STATION_DEFAULT_CARD_STYLE = 'bg-light'
    STATION_ACCEPTED_CARD_STYLE = 'text-success bg-dark'
    STATION_WAITING_CARD_STYLE = 'text-warning bg-dark'
    STATION_PRESELECTED_ACCEPTED_CARD_STYLE = 'text-success bg-dark border-light'
    STATION_PRESELECTED_WAITING_CARD_STYLE = 'text-warning bg-dark border-light'

    TICKET_DEFAULT_CARD_STYLE = 'bg-info text-light'
    TICKET_SELECTED_CARD_STYLE = 'bg-dark text-light'
    PARTY_PRESELECTED_CARD_STYLE = 'text-light bg-dark border-success'
    def __init__(self, form):
        self.form = form

    def station_card_style(self, form_control):
        selection_value = form_control.add.data
        if self.is_station_preselected(form_control):
            weekend_selection = self.weekend_ticket.add.data
            if weekend_selection == FESTIVAL_TICKET.COUPLE:
                form_control.add.data = WORKSHOP_OPTIONS.COUPLE
            else:
                if form_control.add.data not in (WORKSHOP_OPTIONS.LEADER, WORKSHOP_OPTIONS.FOLLOWER):
                    form_control.add.data = WORKSHOP_OPTIONS.LEADER

            selection_value = form_control.add.data

            if form_control.waiting_lists[0][selection_value] == 0:
                return self.STATION_PRESELECTED_ACCEPTED_CARD_STYLE
            else:
                return self.STATION_PRESELECTED_WAITING_CARD_STYLE
        else:
            if selection_value in (WORKSHOP_OPTIONS.LEADER, WORKSHOP_OPTIONS.FOLLOWER, WORKSHOP_OPTIONS.COUPLE):
                if form_control.waiting_lists[0][selection_value] == 0:
                    return self.STATION_ACCEPTED_CARD_STYLE
                else:
                    return self.STATION_WAITING_CARD_STYLE
            else:
                return self.STATION_DEFAULT_CARD_STYLE

    def is_station_preselected(self, form_control):
        if form_control.keywords:
            weekend_ticket = self.weekend_ticket
            if weekend_ticket:
                includes = weekend_ticket.includes.split(',')
                return form_control.keywords in includes
        return False

    def iter_station_choices(self, form_field):
        for choice in form_field.add.iter_choices():
            if choice[0] in (WORKSHOP_OPTIONS.LEADER, WORKSHOP_OPTIONS.FOLLOWER):
                if not self.is_couples_only:
                    yield choice
            elif choice[0] == WORKSHOP_OPTIONS.COUPLE:
                if not self.is_singles_only:
                    yield choice
            else:
                yield choice

    def ticket_card_style(self, form_control):
        selection_value = form_control.add.data
        if selection_value in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE):
            return self.TICKET_SELECTED_CARD_STYLE
        else:
            return self.TICKET_DEFAULT_CARD_STYLE

    def party_card_style(self, form_control):
        if self.is_parties_included:
            form_control.add.data = self.weekend_ticket.add.data
            return self.PARTY_PRESELECTED_CARD_STYLE
        else:
            selection_value = form_control.add.data
            if selection_value in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE):
                return self.TICKET_SELECTED_CARD_STYLE
            else:
                return self.TICKET_DEFAULT_CARD_STYLE


    def radio_field_checked(self, form_field, radio_value, yes='checked'):
        if form_field.add.data == radio_value:
            return yes
        else:
            return ''

    @property
    def weekend_ticket_key(self):
        weekend_tickets_keys = [
            'full_weekend_ticket',
            'full_weekend_ticket_no_parties',
            'fast_train_to_collegiate_shag',
            'fast_train_to_collegiate_shag_no_parties',
            'fast_train_to_st_louis_shag',
            'fast_train_to_st_louis_shag_no_parties',
            'parties_only'
        ]
        for ticket_key in weekend_tickets_keys:
            ticket = self.form.get_product_by_key(ticket_key)
            if ticket.add.data in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE):
                return ticket_key

    @property
    def weekend_ticket(self):
        if self.weekend_ticket_key:
            return self.form.get_product_by_key(self.weekend_ticket_key)

    @property
    def is_couples_only(self):
        weekend_ticket = self.weekend_ticket
        return weekend_ticket and (weekend_ticket.add.data == FESTIVAL_TICKET.COUPLE)

    @property
    def is_singles_only(self):
        weekend_ticket = self.weekend_ticket
        return weekend_ticket and (weekend_ticket.add.data == FESTIVAL_TICKET.SINGLE)

    @property
    def has_couples_tickets(self):
        for ticket_key in self.form.product_keys:
            if self.form.get_product_by_key(ticket_key).add.data == 'couple':
                return True
        else:
            return False

    @property
    def selected_stations_count(self):
        stations = 0
        for ticket_key in self.form.product_keys:
            ticket = self.form.get_product_by_key(ticket_key)
            if ticket.product_type == 'RegularPartnerWorkshop' and ticket.add.data:
                stations += 1
        return stations

    @property
    def full_pass_selected(self):
        return self.form.get_product_by_key('full_weekend_ticket').add.data in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE) or \
               self.form.get_product_by_key('full_weekend_ticket_no_parties').add.data in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE)


    @property
    def is_parties_included(self):
        party_tickets_keys = [
            'full_weekend_ticket',
            'fast_train_to_collegiate_shag',
            'fast_train_to_st_louis_shag',
            'parties_only'
        ]
        weekend_ticket_key = self.weekend_ticket_key
        return weekend_ticket_key and weekend_ticket_key in party_tickets_keys

    @property
    def is_special_extra_block_price(self):
        special_extra_block_price_keys = [
            'full_weekend_ticket',
            'full_weekend_ticket_no_parties',
            'fast_train_to_collegiate_shag',
            'fast_train_to_collegiate_shag_no_parties',
            'fast_train_to_st_louis_shag',
            'fast_train_to_st_louis_shag_no_parties',
        ]
        weekend_ticket_key = self.weekend_ticket_key
        return weekend_ticket_key and weekend_ticket_key in special_extra_block_price_keys

    def line_badges(self, form_field):
        line_styles = {
            'Jitterbug': 'badge-info',
            'Collegiate': 'badge-danger',
            'Collegiate Super': 'badge-danger',
            'St.Louis': 'badge-success'
        }
        lines = form_field.workshop_level.split(',')
        badges = ['<span class="badge badge-pill {}">{}</span>'.format(line_styles[line], line) for line in lines]
        return ' '.join(badges)
