from flask import render_template
from flask import url_for, jsonify
from salty_tickets import app
from salty_tickets import config
from salty_tickets.controllers import OrderSummaryController, OrderProductController, FormErrorController
from salty_tickets.database import db_session
from salty_tickets.email import send_registration_confirmation
from salty_tickets.forms import create_event_form, create_crowdfunding_form, get_registration_from_form, \
    get_partner_registration_from_form, OrderProductCancelForm
from salty_tickets.models import Event, CrowdfundingRegistrationProperties, Registration, RefundRequest
from salty_tickets.pricing_rules import get_order_for_event, get_total_raised, \
    get_order_for_crowdfunding_event, get_stripe_properties, balance_event_waiting_lists, process_partner_registrations
from salty_tickets.tokens import email_deserialize
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
            process_partner_registrations(user_order, form)
            balance_event_waiting_lists(event)
            send_registration_confirmation(user_order)
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
        form_errors_controller = FormErrorController(form)
        return_dict['order_summary_html'] = render_template('form_errors.html',
                                                            form_errors=form_errors_controller)
        return_dict['errors'] = {v:k for v,k in form_errors_controller.errors}
    return jsonify(return_dict)


# @app.route('/register/total_price/<string:event_key>', methods=('POST',))
# def total_price(event_key):
#     event = Event.query.filter_by(event_key=event_key).first()
#     form = create_event_form(event)()
#     if form.validate_on_submit():
#         user_order = get_order_for_event(event, form)
#         price = user_order.total_price
#         return jsonify({'total_price': price, 'order_summary_html': render_template('order_summary.html', order=user_order, price=price)})
#     else:
#         return jsonify({})


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
        form_errors_controller = FormErrorController(form)
        return_dict['order_summary_html'] = render_template('form_errors.html',
                                                            form_errors=form_errors_controller)
        return_dict['errors'] = {v: k for v, k in form_errors_controller.errors}
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


@app.route('/register/<string:event_key>/order/<string:email_token>')
def event_order(event_key, email_token):
    email = email_deserialize(email_token)


@app.route('/register/<string:event_key>/cancel/<string:order_product_token>', methods=('GET', 'POST'))
def event_order_product_cancel(event_key, order_product_token):
    form = OrderProductCancelForm()
    order_product_controller = OrderProductController.from_token(order_product_token)

    if form.validate_on_submit():
        refund_request = RefundRequest()
        refund_request.product_order = order_product_controller._order_product
        db_session.add(refund_request)
        db_session.commit()
        return 'Cancelled'
    else:
        return render_template('cancel_order_product.html',
                               form=form, order_product_controller=order_product_controller)
