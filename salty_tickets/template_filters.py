# from salty_tickets import tickets_app
import jinja2
from salty_tickets.views import tickets_bp


@jinja2.contextfilter
@tickets_bp.app_template_filter('price')
def price_filter(amount: float) -> str:
    return '£{:.2f}'.format(amount)


@jinja2.contextfilter
@tickets_bp.app_template_filter('price_int')
def price_int_filter(amount: float) -> str:
    return '£{:.0f}'.format(amount)


@jinja2.contextfilter
@tickets_bp.app_template_filter('price_stripe')
def price_stripe_filter(amount: float) -> str:
    return '{:.0f}'.format(amount*100)
