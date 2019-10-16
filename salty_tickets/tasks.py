import logging
import dramatiq
from config import EMAIL_FROM
from flask import render_template, url_for, current_app
from salty_tickets.dao import TicketsDAO
from salty_tickets.emails import send_email
from salty_tickets.tokens import RegistrationToken, PaymentId

def get_dao():
    return TicketsDAO(current_app.config['MONGO'])

@dramatiq.actor(priority=5)
def task_registration_confirmation_email(payment_id, event_key):
    dao = get_dao()
    payment = dao.get_payment_by_id(payment_id)
    if payment is None:
        logging.error(f'Payment {payment_id} not found')
        return

    event = dao.get_event_by_key(event_key)
    if event is None:
        logging.error(f'Event {event_key} not found')
        return

    with current_app.app_context():
        order_status_url = url_for('tickets_bp.user_order_index', pmt_token=PaymentId().serialize(payment), _external=True)
        order_update_url = url_for('tickets_bp.event_index', event_key=event.key,
                                   reg_token=RegistrationToken().serialize(payment.paid_by), _external=True)

        # ptn_token = PartnerToken().serialize(payment.paid_by)
        body_text = render_template('email/registration_confirmation.txt',
                                    payment=payment,
                                    event=event,
                                    # ptn_token=ptn_token,
                                    order_status_url=order_status_url,
                                    order_update_url=order_update_url,
                                    # order_update_url=order_status_url,
                                    )

    subj = f'{event.name} - Registration'

    res = send_email(EMAIL_FROM, payment.paid_by.email, subj, body_text, body_html=None)
    logging.info(res)
    return res


@dramatiq.actor(priority=20)
def task_waiting_list_accept_email(registration_id):
    dao = get_dao()
    registration = dao.get_ticket_registration_by_id(registration_id)
    if registration is None:
        logging.error(f'Registration {registration_id} not found')
        return
    payment = dao.get_payment_by_registration(registration)
    event = dao.get_payment_event(payment)
    with current_app.app_context():
        order_status_url = url_for('tickets_bp.user_order_index', pmt_token=PaymentId().serialize(payment), _external=True)
        body_text = render_template('email/acceptance_from_waiting_list.txt',
                                    registration=registration,
                                    event=event,
                                    order_status_url=order_status_url)

    subj = f'{event.name} - You are in!'

    res = send_email(EMAIL_FROM, registration.person.email, subj, body_text, body_html=None)
    logging.info(res)
    return res


@dramatiq.actor(priority=10)
def task_balance_waiting_lists(event_key):
    dao = get_dao()
    event = dao.get_event_by_key(event_key)
    if event is None:
        logging.error(f'Event {event_key} not found')
        return
    from salty_tickets.api.registration_process import balance_event_waiting_lists
    balance_event_waiting_lists(dao, event.key)


@dramatiq.actor(priority=0)
def task_update_ticket_numbers(event_key):
    dao = get_dao()
    event = dao.get_event_by_key(event_key)
    if event is None:
        logging.error(f'Event {event_key} not found')
        return
    ticket_registrations = dao.get_ticket_registrations(event)

    ticket_numbers = {k: t.calculate_ticket_numbers(ticket_registrations[k])
                      for k, t in event.tickets.items()}
    dao.save_event_ticket_numbers(event_key, ticket_numbers)
