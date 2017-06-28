from flask import render_template, request
from flask import url_for, jsonify
from itsdangerous import BadSignature
from salty_tickets import app
from salty_tickets import config
from salty_tickets.controllers import OrderSummaryController, OrderProductController, FormErrorController
from salty_tickets.database import db_session
from salty_tickets.emails import send_registration_confirmation, send_cancellation_request_confirmation
from salty_tickets.forms import create_event_form, create_crowdfunding_form, get_registration_from_form, \
    get_partner_registration_from_form, OrderProductCancelForm, VoteForm, VoteAdminForm
from salty_tickets.models import Event, CrowdfundingRegistrationProperties, Registration, RefundRequest, Order, Vote, \
    VotingSession
from salty_tickets.pricing_rules import get_order_for_event, get_total_raised, \
    get_order_for_crowdfunding_event, get_stripe_properties, balance_event_waiting_lists, process_partner_registrations
from salty_tickets.products import flip_role
from salty_tickets.tokens import email_deserialize, order_product_deserialize, order_deserialize, order_serialize
from sqlalchemy import desc
from werkzeug.utils import redirect

__author__ = 'vnkrv'


@app.route('/')
def index():
    return redirect(url_for('register_index'))
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
            balance_results = balance_event_waiting_lists(event)
            email_result = send_registration_confirmation(user_order)
            # order_summary_controller = OrderSummaryController(user_order)
            # return render_template('signup_thankyou.html', order_summary_controller=order_summary_controller,
            #                        event_key=event.event_key)
            return redirect(url_for('signup_thankyou', order_token=order_serialize(user_order)))
        else:
            print(response)
            return render_template('event_purchase_error.html', error_message=response)

    tokens = request.args.get('tokens')
    if tokens:
        tokens = tokens.split(',')
        for token in tokens:
            try:
                order_product = order_product_deserialize(token)
                if order_product.order.event.id == event.id:
                    form[order_product.product.product_key].partner_token.data = token
                    form[order_product.product.product_key].dance_role.data = flip_role(order_product.details_as_dict['dance_role'])
                    form[order_product.product.product_key].add.data = 1
            except BadSignature:
                pass
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
        return_dict['validated_partner_tokens'] = get_validated_partner_tokens(form)
    else:
        form_errors_controller = FormErrorController(form)
        return_dict['order_summary_html'] = render_template('form_errors.html',
                                                            form_errors=form_errors_controller)
        return_dict['errors'] = {v:k for v,k in form_errors_controller.errors}
    return jsonify(return_dict)


def get_validated_partner_tokens(form):
    tokens_data = {}
    for product_key in form.product_keys:
        product_form = form.get_product_by_key(product_key)
        if hasattr(product_form, 'partner_token'):
            if product_form.partner_token.data:
                order_product = order_product_deserialize(product_form.partner_token.data)
                tokens_data[product_form.partner_token.id] = 'Your partner: {}'.format(order_product.registrations[0].name)
    return tokens_data


# @app.route('/register/thankyou/<string:event_key>', methods=('GET', 'POST'))
# def signup_thankyou(event_key):
#     return render_template('signup_thankyou.html', event_key=event_key)


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
        success, response = user_order.charge(form.stripe_token.data, stripe_sk=config.STRIPE_SIMONA_SK)
        if success:
            db_session.commit()
            return redirect(url_for('crowdfunding_thankyou', event_key=event.event_key))
        else:
            print(response)
            return render_template('event_purchase_error.html', error_message=response)

    contributors = Registration.query.\
        join(Order, aliased=True).join(Event, aliased=True).filter_by(event_key=event_key).\
        order_by(desc(Registration.registered_datetime)).all()
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
        send_cancellation_request_confirmation(order_product_controller._order_product)
        return 'Cancel request has been submitted'
    else:
        return render_template('cancel_order_product.html',
                               form=form, order_product_controller=order_product_controller)


@app.route('/register/order/<string:order_token>')
def event_order_summary(order_token):
    return render_event_order_summary(order_token, title="Order Status")


@app.route('/register/thankyou/<string:order_token>')
def signup_thankyou(order_token):
    return render_event_order_summary(order_token, title="Thank you for Registration!")


def render_event_order_summary(order_token, title=None):
    try:
        user_order = order_deserialize(order_token)
    except BadSignature:
        return 'Incorrect order token'

    order_summary_controller = OrderSummaryController(user_order)
    return render_template('signup_thankyou.html', order_summary_controller=order_summary_controller, title=title)


@app.route('/vote')
def vote():
    form = VoteForm()
    return render_template('voting/vote.html', form=form)


@app.route('/vote/submit', methods=['POST'])
def vote_submit():
    form = VoteForm()
    if form.validate_on_submit():
        print(form.csrf_token, form.options.data)
        vote = Vote(voter_id=form.client_fingerprint.data, vote=form.options.data)
        db_session.add(vote)
        db_session.commit()
        return 'Success'
    else:
        return jsonify(form.errors)
        # return 'Something went wrong'


@app.route('/vote/admin', methods=['GET', 'POST'])
def vote_admin():
    form = VoteAdminForm()
    voting_session = VotingSession.query.order_by(VotingSession.id.desc()).first()
    if form.validate_on_submit():
        print(form.start_voting.data)
        print(form.stop_voting.data)
        if form.start_voting.data:
            voting_session = VotingSession(name=form.name.data)
            db_session.add(voting_session)
            db_session.commit()
        elif form.stop_voting.data:
            voting_session.stop()
            db_session.commit()

    if voting_session:
        form.name.data = voting_session.name
        if voting_session.end_timestamp:
            form.stop_voting.data = True
        votes_query = Vote.query.filter(Vote.vote_timestamp > voting_session.start_timestamp)
        if voting_session.end_timestamp:
            votes_query = votes_query.filter(Vote.vote_timestamp < voting_session.end_timestamp)
        all_votes = votes_query.all()
        all_votes_dict = {v.voter_id:v.vote for v in all_votes}

        print(all_votes_dict)

        res_left = len([k for k,v in all_votes_dict.items() if v=='left'])
        res_right = len([k for k,v in all_votes_dict.items() if v=='right'])
        results_data = {
            'left': res_left,
            'right': res_right
        }
    else:
        results_data = None
    return render_template('voting/admin.html', form=form, results_data=results_data)