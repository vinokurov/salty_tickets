import datetime
import mock

import pytest
from salty_tickets.forms import create_event_form, SignupForm, FormWithProducts
from salty_tickets.products import CouplesOnlyWorkshop, RegularPartnerWorkshop, WorkshopRegStats
from salty_tickets.models import Product, Event, DANCE_ROLE_LEADER, DANCE_ROLE_FOLLOWER
from wtforms import Form


def test_CouplesOnlyWorkshop_get_discount_price():
    product = CouplesOnlyWorkshop(
        name='Aerials Workshop - Morning',
        info='Sunday morning aerials workshop with Pol & Sara.',
        max_available=10,
        price=25,
        discount_prices='{"aerials_full_day": 20}'
    )

    form = product.get_form()

    form.add.data = False
    assert product.get_discount_price_by_key('aerials_full_day') == 20


def test_CouplesOnlyWorkshop_get_total_price():
    event = Event(
        name='Salty Recipes with Pol & Sara',
        start_date=datetime.datetime(2017, 7, 29),
        event_type='dance'
    )

    product1 = CouplesOnlyWorkshop(
        name='Aerials Workshop - Morning',
        info='Sunday morning aerials workshop with Pol & Sara.',
        max_available=10,
        price=50,
        discount_prices='{"aerials_full_day": 40}'
    )
    product2 = CouplesOnlyWorkshop(
        name='Aerials Workshop - Afternoon',
        info='Sunday morning aerials workshop with Pol & Sara.',
        max_available=10,
        price=45,
        discount_prices='{"aerials_full_day": 30}'
    )

    event.products.append(product1.model)
    event.products.append(product2.model)

    product1_key = product1.model.product_key
    product1_form = product1.get_form()

    product2_key = product2.model.product_key
    product2_form = product2.get_form()

    class EventForm(Form, FormWithProducts):
        product_keys = [product1_key, product2_key]

    setattr(EventForm, product1_key, product1_form)
    setattr(EventForm, product2_key, product2_form)

    order_form = EventForm()

    order_form.get_product_by_key(product1_key).add.data = False
    order_form.get_product_by_key(product2_key).add.data = False
    assert product1.get_total_price(product1_form, order_form) == 0

    order_form.get_product_by_key(product1_key).add.data = True
    order_form.get_product_by_key(product2_key).add.data = False
    assert product1._get_discount_keys() == ['aerials_full_day']
    assert product1._get_applicable_discount_keys(product1_form, order_form) == []
    assert product1.get_total_price(product1_form, order_form) == 50

    order_form.get_product_by_key(product1_key).add.data = True
    order_form.get_product_by_key(product2_key).add.data = True
    assert product1._get_discount_keys() == ['aerials_full_day']
    assert product1._get_applicable_discount_keys(product1_form, order_form) == ['aerials_full_day']
    assert product1.get_total_price(product1_form, order_form) == 40
    assert product2.get_total_price(product2_form, order_form) == 30


@mock.patch.object(RegularPartnerWorkshop, 'get_registration_stats')
def test_RegularPartnerWorkshop_get_waiting_lists(get_registration_stats):

    product_model = mock.Mock(spec=Product)

    def test_case(max_available, ratio, allow_first,
                  leads_acc, follows_acc, leads_wait, follows_wait,
                  res_leads, res_follows, res_leads_with_partn, res_follows_with_partn):
        product_model.max_available = max_available
        product_model.parameters_as_dict = {'ratio': ratio, 'allow_first': allow_first}
        get_registration_stats.side_effect = lambda x: {DANCE_ROLE_LEADER: WorkshopRegStats(leads_acc, leads_wait),
                                                        DANCE_ROLE_FOLLOWER: WorkshopRegStats(follows_acc, follows_wait)}
        expected_result = {DANCE_ROLE_LEADER: res_leads, DANCE_ROLE_FOLLOWER: res_follows}, \
                          {DANCE_ROLE_LEADER: res_leads_with_partn, DANCE_ROLE_FOLLOWER: res_follows_with_partn}
        print(RegularPartnerWorkshop.get_waiting_lists(product_model))
        assert RegularPartnerWorkshop.get_waiting_lists(product_model) == expected_result

    # no registrations yet => all available
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=0, follows_acc=0, leads_wait=0, follows_wait=0,
              res_leads=0, res_follows=0, res_leads_with_partn=0, res_follows_with_partn=0)

    # no free spaces => all waiting list
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=20, follows_acc=20, leads_wait=0, follows_wait=0,
              res_leads=1, res_follows=1, res_leads_with_partn=1, res_follows_with_partn=1)

    # just one place available, class balanced => ??
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=19, follows_acc=20, leads_wait=0, follows_wait=0,
              res_leads=0, res_follows=0, res_leads_with_partn=1, res_follows_with_partn=0)

    # imbalanced class, but before {allow_first} => all ok
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=3, follows_acc=4, leads_wait=0, follows_wait=0,
              res_leads=0, res_follows=0, res_leads_with_partn=0, res_follows_with_partn=0)

    # imbalanced class, more than {allow first} => apply restrictions
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=9, follows_acc=12, leads_wait=0, follows_wait=0,
              res_leads=0, res_follows=1, res_leads_with_partn=0, res_follows_with_partn=0)

    # followers waiting list exist => followers waiting list +1
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=9, follows_acc=12, leads_wait=0, follows_wait=2,
              res_leads=0, res_follows=3, res_leads_with_partn=0, res_follows_with_partn=0)

    # followers waiting list exist, before {allow first} => followers waiting list +1
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=3, follows_acc=4, leads_wait=0, follows_wait=5,
              res_leads=0, res_follows=6, res_leads_with_partn=0, res_follows_with_partn=0)

    # class imbalanced, followers wait list equal to remaining places => followers waiting list +1
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=15, follows_acc=20, leads_wait=0, follows_wait=5,
              res_leads=0, res_follows=6, res_leads_with_partn=0, res_follows_with_partn=0)

    # still remaining places, but followers - max => waiting list for solo and partnered followers
    test_case(max_available=40, ratio=1.35, allow_first=10,
              leads_acc=15, follows_acc=23, leads_wait=0, follows_wait=5,
              res_leads=0, res_follows=6, res_leads_with_partn=0, res_follows_with_partn=1)



