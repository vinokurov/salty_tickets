from typing import List, Dict

from salty_tickets.models.event import Event
from salty_tickets.models.products import BaseProduct
from salty_tickets.models.registrations import ProductRegistration


def validate_registrations(event: Event, registrations: List[ProductRegistration]):
    errors = {}
    for rule in event.validation_rules:
        rule_func = VALIDATION_RULES[rule['name']]
        _error = rule_func(registrations, event.products, **rule['kwargs'])
        if _error:
            errors['Registration'] = [_error]
    return errors


def errors_at_least_any_with_tag(registrations: List[ProductRegistration],
                                 products: Dict[str, BaseProduct],
                                 tag, count=1, error_text=None):
    primary = registrations[0].registered_by
    matching_products = [products[r.product_key] for r in registrations
                         if tag in products[r.product_key].tags
                         and r.person == primary]
    if 0 < len(matching_products) < count:
        return error_text

    partner_products = [products[r.product_key] for r in registrations
                         if tag in products[r.product_key].tags
                         and r.person != primary]
    if 0 < len(partner_products) < count:
        return error_text


def errors_if_overlapping(registrations: List[ProductRegistration],
                          products: Dict[str, BaseProduct],
                          tag, error_text=None):
    primary = registrations[0].registered_by
    matching_products = [products[r.product_key] for r in registrations
                         if tag in products[r.product_key].tags
                         and r.person == primary]
    start_times = [p.start_datetime for p in matching_products if hasattr(p, 'start_datetime')]
    if len(start_times) > len(set(start_times)):
        return error_text

    partner_products = [products[r.product_key] for r in registrations
                         if tag in products[r.product_key].tags
                         and r.person != primary]
    start_times = [p.start_datetime for p in partner_products if hasattr(p, 'start_datetime')]
    if len(start_times) > len(set(start_times)):
        return error_text


VALIDATION_RULES = {
    'at_least_any_with_tag': errors_at_least_any_with_tag,
    'non_overlapping': errors_if_overlapping,
}
