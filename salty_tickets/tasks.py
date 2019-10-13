import logging

from salty_tickets import dramatiq
from config import EMAIL_FROM
from flask import render_template, url_for, current_app
from salty_tickets.dao import TicketsDAO
from salty_tickets.emails import send_email
from salty_tickets.tokens import RegistrationToken, PaymentId

dao = TicketsDAO(current_app.config['MONGO'])

@dramatiq.actor
def task_registration_confirmation_email(payment_id, event_key):
    payment = dao.get_payment_by_id(payment_id)
    event = dao.get_event_by_key(event_key)
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


@dramatiq.actor
def task_waiting_list_accept_email(registration_id):
    registration = dao.get_ticket_registration_by_id(registration_id)
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


@dramatiq.actor
def task_balance_waiting_lists(event_key):
    from salty_tickets.api.registration_process import balance_event_waiting_lists
    balance_event_waiting_lists(dao, event_key)
