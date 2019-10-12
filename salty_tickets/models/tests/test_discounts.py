from flask import Flask as _Flask
import pytest
from salty_tickets.forms import create_event_form
from salty_tickets.models.discounts import FixedValueDiscountProduct, CodeDiscountProduct, FreeRegistrationDiscountRule, \
    FreePartiesDiscountRule, FreeFullPassDiscountRule
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment, Person, Registration, Discount
from salty_tickets.models.tickets import WorkshopTicket, PartyTicket, FestivalPassTicket


class Flask(_Flask):
    testing = True
    secret_key = __name__

    def make_response(self, rv):
        if rv is None:
            rv = ''

        return super(Flask, self).make_response(rv)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def festival_event():
    tickets = [
        WorkshopTicket(name='W1', tags={'workshop'}),
        WorkshopTicket(name='W2', tags={'workshop'}),
        WorkshopTicket(name='W3', tags={'workshop'}),
        PartyTicket(name='P1', tags={'party'}, base_price=20),
        PartyTicket(name='P2', tags={'party'}, base_price=25),
        PartyTicket(name='P3', tags={'party'}, base_price=15),
        FestivalPassTicket(name='Full Pass', tags={'pass', 'includes_parties', 'discount'}, base_price=120),
        FestivalPassTicket(name='Fast Train', tags={'pass', 'includes_parties', 'discount'}, base_price=90),
        FestivalPassTicket(name='Fast Train no parties', tags={'pass'}, base_price=40),
        FestivalPassTicket(name='Party Pass', tags={'party_pass', 'includes_parties'}, base_price=50),
    ]
    event = Event(
        name='Test Festival',
        tickets={t.key: t for t in tickets}
    )
    return event


@pytest.fixture
def mr_x():
    return Person('Mr.X', 'mr.x@gmail.com')


@pytest.fixture
def ms_y():
    return Person('Ms.Y', 'ms.y@gmail.com')


@pytest.mark.parametrize('x_registrations,y_registrations,x_discount,y_discount', [
    ([('full_pass', 120)], [], 10, None),
    ([('w1', 35)], [], None, None),
    ([('w1', 35), ('w2', 35)], [], None, None),
    ([('w1', 35), ('w2', 35), ('full_pass', 120)], [], 10, None),
    ([('full_pass', 120)], [('full_pass', 120)], 10, 10),
    ([('w1', 35), ('w2', 35), ('full_pass', 120)], [('w1', 35)], 10, None),
    ([('w1', 35), ('w2', 35), ('full_pass', 120)], [('w1', 35), ('full_pass', 120)], 10, 10),
])
def test_FixedValueDiscountProduct(app, festival_event, mr_x, ms_y,
                                   x_registrations, y_registrations, x_discount, y_discount):
    registrations = [Registration(person=mr_x, ticket_key=i[0], price=i[1]) for i in x_registrations] \
                    + [Registration(person=ms_y, ticket_key=i[0], price=i[1]) for i in y_registrations]
    payment = Payment(
        paid_by=mr_x,
        registrations=registrations
    )
    discount_product = FixedValueDiscountProduct(
        name='Test Discount',
        info='A test discount',
        discount_value=10,
        tag='discount'
    )
    festival_event.discount_products = {discount_product.key: discount_product}
    with app.app_context():
        form = create_event_form(festival_event)()
    assert [] == discount_product.get_discount(festival_event.tickets, payment, form)

    form.get_item_by_key('test_discount').validated.data = True
    expected_discounts = []
    if x_discount is not None:
        expected_discounts.append(Discount(person=mr_x, discount_key=discount_product.key,
                                           value=x_discount, description=discount_product.info))
    if y_discount is not None:
        expected_discounts.append(Discount(person=ms_y, discount_key=discount_product.key,
                                           value=y_discount, description=discount_product.info))
    assert expected_discounts == discount_product.get_discount(festival_event.tickets, payment, form)


@pytest.mark.parametrize('x_registrations,y_registrations,x_discount,y_discount', [
    ([('full_pass', 120)], [], 120, None),
    ([('w1', 35)], [], 35, None),
    ([('w1', 35), ('w2', 35)], [], 70, None),
    ([('w1', 0), ('w2', 0), ('full_pass', 120)], [], 120, None),
    ([('full_pass', 120)], [('full_pass', 120)], 120, 120),
    ([('w1', 0), ('w2', 0), ('full_pass', 120)], [('w1', 35)], 120, 35),
    ([('w1', 0), ('w2', 0), ('full_pass', 120)], [('w1', 0), ('full_pass', 120)], 120, 120),
])
def test_FreeRegistrationDiscountRule(app, festival_event, mr_x, ms_y,
                                      x_registrations, y_registrations, x_discount, y_discount):
    discount_rule = FreeRegistrationDiscountRule(info='Free registration')
    discount_rule_testing_procedure(app, discount_rule, mr_x, ms_y, festival_event,
                                    x_discount, x_registrations, y_discount, y_registrations)


@pytest.mark.parametrize('x_registrations,y_registrations,x_discount,y_discount', [
    ([('party_pass', 50)], [], 50, None),
    ([('p1', 20)], [], 20, None),
    ([('p1', 20), ('p2', 25)], [], 45, None),
    ([('p1', 20), ('p2', 25), ('w1', 30)], [], 45, None),
    ([('w1', 35)], [], None, None),
    ([('full_pass', 120)], [], 50, None),
    ([('fast_train', 90)], [], 50, None),
    ([('fast_train_no_parties', 40)], [], None, None),

    ([('party_pass', 50)], [('party_pass', 50)], 50, 50),
    ([('party_pass', 50)], [('w1', 30)], 50, None),
    ([('p1', 20), ('p2', 25), ('w1', 30)], [('p2', 25), ('w1', 30)], 45, 25),
    ([('full_pass', 120)], [('full_pass', 120)], 50, 50),
    ([('full_pass', 120)], [('w1', 30)], 50, None),

    ([('fast_train', 40)], [], None, None),
])
def test_FreePartiesDiscountRule(app, festival_event, mr_x, ms_y,
                                 x_registrations, y_registrations, x_discount, y_discount):
    discount_rule = FreePartiesDiscountRule(info='Free party pass')
    discount_rule_testing_procedure(app, discount_rule, mr_x, ms_y, festival_event,
                                    x_discount, x_registrations, y_discount, y_registrations)


@pytest.mark.parametrize('x_registrations,y_registrations,x_discount,y_discount', [
    ([('full_pass', 120)], [], 120, None),
    ([('fast_train', 90)], [], 90, None),
    ([('fast_train_no_parties', 40)], [], 40, None),
    ([('fast_train', 60)], [], 60, None),
    ([('fast_train', 120), ('w1', 25)], [], 120, None),
    ([('party_pass', 50)], [], None, None),
    ([('w1', 30)], [], None, None),

    ([('full_pass', 120)], [('full_pass', 120)], 120, 120),
    ([('full_pass', 120)], [('party_pass', 50)], 120, None),
])
def test_FreeFullPassDiscountRule(app, festival_event, mr_x, ms_y,
                                  x_registrations, y_registrations, x_discount, y_discount):
    discount_rule = FreeFullPassDiscountRule(info='Free full pass')
    discount_rule_testing_procedure(app, discount_rule, mr_x, ms_y, festival_event,
                                    x_discount, x_registrations, y_discount, y_registrations)


def discount_rule_testing_procedure(app, discount_rule, mr_x, ms_y, festival_event,
                                    x_discount, x_registrations, y_discount, y_registrations):
    registrations = [Registration(person=mr_x, ticket_key=i[0], price=i[1]) for i in x_registrations] \
                    + [Registration(person=ms_y, ticket_key=i[0], price=i[1]) for i in y_registrations]
    payment = Payment(
        paid_by=mr_x,
        registrations=registrations
    )
    discount_product = CodeDiscountProduct(
        name='Test Discount',
        discount_rule=discount_rule
    )
    festival_event.discount_products = {discount_product.key: discount_product}
    with app.app_context():
        form = create_event_form(festival_event)()
    assert [] == discount_product.get_discount(festival_event.tickets, payment, form)
    form.get_item_by_key('test_discount').validated.data = True
    expected_discounts = []
    if x_discount is not None:
        expected_discounts.append(Discount(person=mr_x, value=x_discount, discount_key=discount_product.key,
                                           description=discount_product.discount_rule.info))
    assert expected_discounts == discount_product.get_discount(festival_event.tickets, payment, form)
    discount_product.applies_to_couple = True
    if y_discount is not None:
        expected_discounts.append(Discount(person=ms_y, value=y_discount, discount_key=discount_product.key,
                                           description=discount_product.discount_rule.info))
    assert expected_discounts == discount_product.get_discount(festival_event.tickets, payment, form)
