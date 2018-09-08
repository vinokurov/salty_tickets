from salty_tickets.template_filters import price_filter, price_int_filter, price_stripe_filter


def test_price_filter(app):
    assert '£20.21' == price_filter(20.21)


def test_price_int_filter(app):
    assert '£20' == price_int_filter(20.21)


def test_price_stripe_filter(app):
    assert '2021' == price_stripe_filter(20.21)
