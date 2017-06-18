from logging import Logger

import logging
from flask import render_template
from flask import url_for, jsonify
from premailer import Premailer
from premailer import transform
from salty_tickets import app
from salty_tickets import config
from salty_tickets.controllers import OrderSummaryController
from salty_tickets.database import db_session
from salty_tickets.email import send_email
from salty_tickets.forms import create_event_form, create_crowdfunding_form, get_registration_from_form, \
    get_partner_registration_from_form
from salty_tickets.models import Event, Order, CrowdfundingRegistrationProperties, Registration
from salty_tickets.pricing_rules import get_salty_recipes_price, get_order_for_event, get_total_raised, \
    get_order_for_crowdfunding_event, get_stripe_properties, balance_event_waiting_lists
from salty_tickets.tokens import token_to_email
from werkzeug.utils import redirect

__author__ = 'vnkrv'


@app.route('/')
def index():
    return redirect(url_for('crowdfunding_index'))
    # return render_template('index.html')
    # event = Event.query.filter_by(active=True, event_type='dance').order_by(Event.start_date).first()
    # if event:
    #     return redirect(url_for('register_form', event_key=event.event_key))


@app.route('/r')
@app.route('/register')
@app.route('/register/')
def register_index():
    event = Event.query.filter_by(active=True, event_type='dance').order_by(Event.start_date).first()
    if event:
        return redirect(url_for('register_form', event_key=event.event_key))


@app.route('/register/<string:event_key>', methods=('GET', 'POST'))
def register_form(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_event_form(event)()

    if form.validate_on_submit():
        registration = get_registration_from_form(form)
        partner_registration = get_partner_registration_from_form(form)
        user_order = get_order_for_event(event, form, registration, partner_registration)
        user_order.registration = registration
        event.orders.append(user_order)
        db_session.commit()
        success, response = user_order.charge(form.stripe_token.data)
        if success:
            db_session.commit()
            balance_event_waiting_lists(event)
            return redirect(url_for('signup_thankyou', event_key=event.event_key))
        else:
            return response

    return render_template('signup.html', event=event, form=form, config=config)


@app.route('/register/checkout/<string:event_key>', methods=['POST'])
def register_checkout(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_event_form(event)()

    return_dict = dict(errors={})

    if form.validate_on_submit():
        registration = get_registration_from_form(form)
        partner_registration = get_partner_registration_from_form(form)
        user_order = get_order_for_event(event, form, registration, partner_registration)
        return_dict['stripe'] = get_stripe_properties(event, user_order, form)
        order_summary_controller = OrderSummaryController(user_order)
        return_dict['order_summary_html'] = render_template('order_summary.html',
                                                            order_summary_controller=order_summary_controller)
    else:
        print(form.errors)
        return_dict['order_summary_html'] = render_template('form_errors.html', form_errors=form.errors)
        return_dict['errors'] = form.errors
    return jsonify(return_dict)


@app.route('/register/total_price/<string:event_key>', methods=('POST',))
def total_price(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_event_form(event)()
    if form.validate_on_submit():
        user_order = get_order_for_event(event, form)
        price = user_order.total_price
        return jsonify({'total_price': price, 'order_summary_html': render_template('order_summary.html', order=user_order, price=price)})
    else:
        return jsonify({})


@app.route('/register/thankyou/<string:event_key>', methods=('GET', 'POST'))
def signup_thankyou(event_key):
    return render_template('signup_thankyou.html', event_key=event_key)


@app.route('/c')
@app.route('/crowdfunding')
@app.route('/crowdfunding/')
def crowdfunding_index():
    event = Event.query.filter_by(active=True, event_type='crowdfunding').order_by(Event.start_date).first()
    if event:
        return redirect(url_for('crowdfunding_form', event_key=event.event_key))


@app.route('/crowdfunding/<string:event_key>', methods=('GET', 'POST'))
def crowdfunding_form(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_crowdfunding_form(event)()

    total_stats = get_total_raised(event)

    if form.validate_on_submit():
        registration = get_registration_from_form(form)
        registration.crowdfunding_registration_properties = \
                CrowdfundingRegistrationProperties(anonymous=form.anonymous.data)
        # partner_registration = get_partner_registration_from_form(form)
        user_order = get_order_for_crowdfunding_event(event, form, registration, None)
        user_order.registration = registration
        event.orders.append(user_order)
        db_session.commit()
        success, response = user_order.charge(form.stripe_token.data)
        if success:
            db_session.commit()
            return redirect(url_for('crowdfunding_thankyou', event_key=event.event_key))
        else:
            return response

    contributors = Registration.query.join(event.orders).all()
    return render_template(
        'crowdfunding.html',
        event=event,
        form=form,
        total_stats=total_stats,
        contributors=contributors,
        config=config
    )


@app.route('/crowdfunding/checkout/<string:event_key>', methods=['POST'])
def crowdfunding_checkout(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_crowdfunding_form(event)()

    return_dict = dict(errors={})

    if form.validate_on_submit():
        registration = get_registration_from_form(form)
        user_order = get_order_for_crowdfunding_event(event, form, registration, None)
        return_dict['stripe'] = get_stripe_properties(event, user_order, form)
        order_summary_controller = OrderSummaryController(user_order)
        return_dict['order_summary_html'] = render_template('order_summary.html',
                                                            order_summary_controller=order_summary_controller)
    else:
        print(form.errors)
        return_dict['order_summary_html'] = render_template('form_errors.html', form_errors=form.errors)
        return_dict['errors'] = form.errors
    return jsonify(return_dict)


@app.route('/crowdfunding/thankyou/<string:event_key>', methods=('GET', 'POST'))
def crowdfunding_thankyou(event_key):
    return render_template('crowdfunding_thankyou.html', event_key=event_key)


@app.route('/crowdfunding/contributors/<string:event_key>', methods=['GET'])
def crowdfunding_contributors(event_key):
    pass


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/email')
def confirmation_email():
    html = render_template('email/registration_confirmation.html', event_key='salty_recipes_with_pol_sara', app=app)
    pr = Premailer(html, cssutils_logging_level=logging.CRITICAL)
    html_for_email = pr.transform()
    import re
    html_for_email = re.sub(r'<style.*</style>', '', html_for_email, flags=re.DOTALL)
    print(html_for_email)
    send_email(config.EMAIL_FROM, 'alexander.a.vinokurov@gmail.com', 'Registration successful', 'text body', html_for_email)


@app.route('/register/<string:event_key>/order/<string:email_token>')
def event_order(event_key, email_token):
    email = token_to_email(email_token)
