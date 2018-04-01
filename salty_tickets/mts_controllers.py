import itertools
from flask import url_for
from salty_tickets.controllers import EventController, OrderSummaryController
from salty_tickets.models import RegistrationGroup, OrderProduct, Order, Product, Registration
from salty_tickets.products import WORKSHOP_OPTIONS, FESTIVAL_TICKET, FestivalGroupDiscountProduct
from salty_tickets.tokens import GroupToken, MtsTicketToken


class MtsSignupFormController:
    STATION_DEFAULT_CARD_STYLE = 'bg-light'
    STATION_ACCEPTED_CARD_STYLE = 'text-success bg-dark'
    STATION_WAITING_CARD_STYLE = 'text-warning bg-dark'
    STATION_PRESELECTED_ACCEPTED_CARD_STYLE = 'text-success bg-dark border-light'
    STATION_PRESELECTED_WAITING_CARD_STYLE = 'text-warning bg-dark border-light'
    STATION_SOULD_OUT = 'bg-secondary text-light'

    TICKET_DEFAULT_CARD_STYLE = 'bg-info text-light'
    TICKET_SELECTED_CARD_STYLE = 'bg-dark text-light'
    PARTY_PRESELECTED_CARD_STYLE = 'text-light bg-dark border-success'
    def __init__(self, form):
        self.form = form

    def station_card_style(self, form_control):
        selection_value = form_control.add.data
        if form_control.available_quantity <= 0:
            return self.STATION_SOULD_OUT
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
            'Jitterbug': 'badge-success',
            'Collegiate': 'badge-warning',
            'Collegiate Super': 'badge-warning',
            'St.Louis': 'badge-primary'
        }
        lines = form_field.workshop_level.split(',')
        badges = ['<span class="badge badge-pill {}">{}</span>'.format(line_styles[line], line) for line in lines]
        return ' '.join(badges)

    @property
    def group_form(self):
        return self.form.get_product_by_key('group_discount')

    def get_group(self, event):
        if self.group_form.group_token.data:
            serialiser = GroupToken()
            try:
                return serialiser.deserialize(self.group_form.group_token.data.strip())
            except Exception as e:
                pass

    def is_new_group(self, event):
        return self.get_group is None

    @property
    def is_group_registration(self):
        return self.group_form.add.data and self.group_form.add.data.strip()

    @staticmethod
    def location_str(country, state, city):
        return ', '.join([v for v in [country, state, city] if v])


    def get_state_dict(self, event):
        state_dict = dict(
            checkout=dict(total=1),
            group=dict(
                group_token_error='',
                group_token_found='',
                group_new_error='',
            ),
            products=dict(),
            total_stations=self.total_stations(event),
            remaining_stations=self.remaining_stations(event),
        )

        if self.group_form.group_participation.data == 'existing':
            group = self.get_group(event)
            if group:
                state_dict['group']['group_token_found'] = 'Group found: %s!' % group.name
            elif self.group_form.group_token.data:
                state_dict['group']['group_token_error'] = 'Incorrect group token'
        elif self.group_form.group_participation.data == 'new':
            if self.group_form.group_name.data:
                if RegistrationGroup.query.filter_by(name=self.group_form.group_name.data.strip()).count() > 0:
                    state_dict['group']['group_new_error'] = 'Group already exists'

        # add products
        for product_key in self.form.product_keys:
            product_form = self.form.get_product_by_key(product_key)
            product_dict = dict(
                available=999,
                keywords=[],
                includes=[],
                waitingList=dict(
                    leader=0,
                    follower=0,
                    leaderWithPartner=0,
                    followerWithPartner=0,
                )
            )
            if hasattr(product_form, 'available_quantity'):
                product_dict['available'] = product_form.available_quantity
            elif product_key.startswith('fast_train'):
                product_dict['available'] = self.get_fast_train_available(product_key)
            elif product_key.startswith('full_weekend'):
                product_dict['available'] = self.get_full_weekend_available()
            elif product_key.startswith('parties'):
                product_dict['available'] = min([self.form.get_product_by_key(p).available_quantity for p in self.party_ticket_keys])

            if hasattr(product_form, 'keywords'):
                product_dict['keywords'] = product_form.keywords.split(',')

            if hasattr(product_form, 'includes'):
                product_dict['includes'] = product_form.includes.split(',')

            if hasattr(product_form, 'waiting_lists'):
                waiting_lists = product_form.waiting_lists
                product_dict['waitingList']['leader'] = waiting_lists[0]['leader']
                product_dict['waitingList']['follower'] = waiting_lists[0]['follower']
                product_dict['waitingList']['leaderWithPartner'] = waiting_lists[1]['leader']
                product_dict['waitingList']['followerWithPartner'] = waiting_lists[1]['follower']

            state_dict['products'][product_key] = product_dict

        return state_dict


    @property
    def weekend_ticket_keys(self):
        keys = [pk for pk in self.form.product_keys if pk.startswith('full_weekend') or pk.startswith('fast_train') or pk.startswith('parties')]
        return keys

    @property
    def party_ticket_keys(self):
        keys = [pk for pk in self.form.product_keys if pk.endswith('_party')]
        return keys

    @property
    def station_keys(self):
        weekend_ticket_keys = self.weekend_ticket_keys
        party_ticket_keys = self.party_ticket_keys
        keys = [pk for pk in self.form.product_keys if pk not in weekend_ticket_keys and pk not in party_ticket_keys]
        return keys

    @property
    def not_enough_stations_selected(self):
        if self.full_pass_selected:
            print(self.selected_stations_count)
            return self.selected_stations_count < 3

    def total_stations(self, event):
        total_blocks = OrderProduct.query.filter(OrderProduct.status.in_(('accepted', 'waiting')))\
                                   .join(Order, aliased=False).filter_by(status='paid')\
                                   .join(Product, aliased=False).filter_by(event_id=event.id, type='RegularPartnerWorkshop').count()
        return total_blocks

    def remaining_stations(self, event):
        total_remaining = 0
        for product in Product.query.filter_by(event_id=event.id, type='RegularPartnerWorkshop').all():
            accepted = OrderProduct.query.filter_by(status='accepted').\
                        join(Order, aliased=False).filter_by(status='paid').\
                        join(Product, aliased=False).filter_by(id=product.id).count()
            total_remaining += max(0, product.max_available - accepted)
        return total_remaining

    def get_fast_train_available(self, weekend_ticket_key):
        weekend_ticket_form = self.form.get_product_by_key(weekend_ticket_key)
        includes = weekend_ticket_form.includes.split(',')
        available_items = []
        for product_key in self.form.product_keys:
            product_form = self.form.get_product_by_key(product_key)
            if set(product_form.keywords.split(',')).intersection(includes):
                if hasattr(product_form, 'available_quantity'):
                    available_items.append(product_form.available_quantity)
        return min(available_items)

    def get_full_weekend_available(self):
        available_slots_dict = {}
        for product_key in self.form.product_keys:
            product_form = self.form.get_product_by_key(product_key)
            if product_form.product_type == 'RegularPartnerWorkshop':
                key = product_form.workshop_date + ' ' + product_form.workshop_time
                available_slots_dict[key] = available_slots_dict.get(key, 0) + max(0, product_form.available_quantity)

        available_slots = sorted(available_slots_dict.values())

        available = 0
        while len(available_slots) >= 3:
            available += available_slots[-3]
            available_slots[-1] -= available_slots[-3]
            available_slots[-2] -= available_slots[-3]
            available_slots[-3] -= available_slots[-3]
            available_slots = [x for x in available_slots if x]

        return available

    @staticmethod
    def get_regular_partner_registration(registration):
        """Retrieves a registration object of a partner if all purchases were made with him/her and all products are the same"""
        partner_registration = None
        for order in registration.orders:
            if len(order.order_product_registrations)<2:
                return None
            order_partner_registration = [r for r in order.order_product_registrations if r != registration][0]
            if not partner_registration:
                partner_registration = order_partner_registration
            elif partner_registration != order_partner_registration:
                return None

        if partner_registration:
            my_products = registration.order_products.\
                join(Product, aliased=False).filter(Product.type != 'FestivalGroupDiscountProduct').all()
            partner_products = partner_registration.order_products. \
                join(Product, aliased=False).filter(Product.type != 'FestivalGroupDiscountProduct').all()

            if sorted([p.product.id for p in my_products]) == sorted([p.product.id for p in partner_products]):
                return partner_registration


class MtsTicketController:
    def __init__(self, registration):
        self._registration = registration

    @classmethod
    def from_ticket_token(cls, ticket_token):
        token_serialiser = MtsTicketToken()
        registration = token_serialiser.deserialize(ticket_token)
        return cls(registration)

    @property
    def event(self):
        return EventController(self._registration.event)

    @property
    def order(self):
        return OrderSummaryController(self._registration.order)

    @property
    def name(self):
        return self._registration.name

    @property
    def email(self):
        return self._registration.email

    @property
    def token(self):
        token_serialiser = MtsTicketToken()
        return token_serialiser.serialize(self._registration)

    @property
    def ticket_url(self):
        return url_for('mts_registration_info', ticket_token=self.token)

    @property
    def qr_code_url(self):
        size=200
        return f'https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={self.ticket_url}'

    @property
    def saturday_stations(self):
        filter_func = lambda x: (x.item_type == 'RegularPartnerWorkshop') and (x.date == '7-April-2018')
        sort_func = lambda x: x.date+x.time
        return sorted(self.items(filter_func), key=sort_func)

    @property
    def sunday_stations(self):
        filter_func = lambda x: x.item_type == 'RegularPartnerWorkshop' and x.date == '8-April-2018'
        sort_func = lambda x: x.date + x.time
        return sorted(self.items(filter_func), key=sort_func)

    @property
    def parties(self):
        filter_func = lambda x: x.item_type == 'FestivalPartyProduct'
        sort_func = lambda x: x.date + x.time
        return sorted(self.items(filter_func), key=sort_func)

    def items(self, filter=None):
        for order_product in self._registration.order_products:
            op = MtsOrderProductController(order_product)
            if not filter or filter(op):
                yield op

    @property
    def weekend_ticket(self):
        op = list(self.items(lambda x: x.item_type == 'FestivalTrackProduct'))
        if len(op):
            return op[0]

    @staticmethod
    def peek(iterable):
        if isinstance(iterable, list):
            if len(iterable):
                return iterable[0]
            return None

        try:
            first = next(iterable)
        except StopIteration:
            return None
        return first, itertools.chain([first], iterable)


class MtsOrderProductController:
    def __init__(self, order_product):
        self._order_product = order_product

    @property
    def name(self):
        return self._order_product.product.name

    @property
    def status(self):
        return self._order_product.status

    @property
    def dance_role(self):
        return self._order_product.details_as_dict.get('dance_role') or 'N/A'

    @property
    def time(self):
        return self._order_product.product.parameters_as_dict.get('workshop_time') or \
               self._order_product.product.parameters_as_dict.get('party_time') or ''

    @property
    def date(self):
        return self._order_product.product.parameters_as_dict.get('workshop_date') or \
               self._order_product.product.parameters_as_dict.get('party_date') or ''

    @property
    def location(self):
        return self._order_product.product.parameters_as_dict.get('workshop_location') or \
               self._order_product.product.parameters_as_dict.get('party_location') or ''

    @property
    def item_type(self):
        return self._order_product.product.type
