from flask import render_template, request, Response
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
from salty_tickets.mts_controllers import MtsSignupFormController
from salty_tickets.payments import process_payment
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
    # event = Event.query.filter_by(active=True, event_type='dance').order_by(Event.id).first()
    if event:
        return redirect(url_for('register_form', event_key=event.event_key))


@app.route('/register/<string:event_key>', methods=('GET', 'POST'))
def register_form(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    if not event:
        event = Event.query.\
            filter_by(active=True, event_type='dance').\
            filter(Event.name.startswith(event_key)).first()
        if event:
            return redirect(url_for('register_form', event_key=event.event_key))
        else:
            return redirect(url_for('register_index'))

    form = create_event_form(event)()

    if form.validate_on_submit():
        registration = get_registration_from_form(form)
        partner_registration = get_partner_registration_from_form(form)
        user_order = get_order_for_event(event, form, registration, partner_registration)
        user_order.registration = registration
        event.orders.append(user_order)
        db_session.commit()
        success, response = process_payment(user_order.payments[0], form.stripe_token.data)
        if success:
            process_partner_registrations(user_order, form)
            balance_results = balance_event_waiting_lists(event)
            email_result = send_registration_confirmation(user_order)
            # order_summary_controller = OrderSummaryController(user_order)
            # return render_template('signup_thankyou.html', order_summary_controller=order_summary_controller,
            #                        event_key=event.event_key)
            return redirect(url_for('signup_thankyou', order_token=order_serialize(user_order)))
        else:
            # print(response)
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
    form_controller = MtsSignupFormController(form)
    return render_template('events/{}/signup.html'.format(event_key), event=event, form=form, config=config, form_controller=form_controller)


@app.route('/register/checkout/<string:event_key>', methods=['POST'])
@app.route('/register/checkout/<string:event_key>/<validate>', methods=['POST'])
def register_checkout(event_key, validate='novalidate'):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_event_form(event)()

    return_dict = dict(errors={})

    if validate == 'validate':
        form_check = form.validate_on_submit
    else:
        form_check = form.is_submitted

    if form_check():
        registration = get_registration_from_form(form)
        partner_registration = get_partner_registration_from_form(form)
        user_order = get_order_for_event(event, form, registration, partner_registration)
        return_dict['stripe'] = get_stripe_properties(event, user_order, form)
        order_summary_controller = OrderSummaryController(user_order)
        return_dict['order_summary_html'] = render_template('order_summary.html',
                                                            order_summary_controller=order_summary_controller)
        return_dict['validated_partner_tokens'] = get_validated_partner_tokens(form)
        return_dict['disable_checkout'] = user_order.order_products.count() == 0
        return_dict['order_summary_total'] = price_filter(order_summary_controller.total_to_pay)
        if event_key == 'mind_the_shag_2018':
            form_controller = MtsSignupFormController(form)
            return_dict['signup_form_html'] = render_template('events/mind_the_shag_2018/mts_signup_form.html',
                                                         event=event, form=form, config=config, form_controller=form_controller)
        print(
            form.name.data,
            request.remote_addr,
            [(payment_item.product.name, price_filter(payment_item.amount), payment_item.product.status) for payment_item in order_summary_controller.payment_items]

        )
    else:
        form_errors_controller = FormErrorController(form)
        return_dict['order_summary_html'] = render_template('form_errors.html',
                                                            form_errors=form_errors_controller)
        return_dict['errors'] = {v:k for v,k in form_errors_controller.errors}
        return_dict['disable_checkout'] = True
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
@app.route('/crowdfunding_campaign')
def crowdfunding_index():
    event = Event.query.filter_by(active=True, event_type='crowdfunding').order_by(Event.start_date).first()
    if event:
        return redirect(url_for('crowdfunding_form', event_key=event.event_key))
    else:
        return redirect('/')


@app.route('/crowdfunding/<string:event_key>', methods=('GET', 'POST'))
def crowdfunding_form(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    if not event:
        event = Event.query.\
            filter_by(active=True, event_type='crowdfunding').\
            filter(Event.name.startswith(event_key)).first()
        if event:
            return redirect(url_for('crowdfunding_form', event_key=event.event_key))
        else:
            return redirect(url_for('crowdfunding_index'))

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
        success, response = process_payment(user_order.payments[0], form.stripe_token.data)
        if success:
            return redirect(url_for('crowdfunding_thankyou', event_key=event.event_key))
        else:
            # print(response)
            return render_template('event_purchase_error.html', error_message=response)

    contributors = Registration.query.\
        join(Order, aliased=True).join(Event, aliased=True).filter_by(event_key=event_key).\
        order_by(desc(Registration.registered_datetime)).all()
    return render_template(
        'events/{}/crowdfunding.html'.format(event_key),
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
        return_dict['disable_checkout'] = user_order.order_products.count() == 0
    else:
        form_errors_controller = FormErrorController(form)
        return_dict['order_summary_html'] = render_template('form_errors.html',
                                                            form_errors=form_errors_controller)
        return_dict['errors'] = {v: k for v, k in form_errors_controller.errors}
        return_dict['disable_checkout'] = True
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


VOTER_UUID_COOKIE_NAME = 'voter'


@app.route('/vote')
def vote():
    form = VoteForm()
    return render_template('voting/vote.html', form=form)


@app.route('/vote/submit', methods=['POST'])
def vote_submit():
    form = VoteForm()
    if form.validate_on_submit():
        voter_uuid = form.client_fingerprint.data
        vote = Vote(voter_id=voter_uuid, vote=form.options.data)
        db_session.add(vote)
        db_session.commit()
        return 'Success'
    else:
        return jsonify(form.errors)


@app.route('/vote/admin', methods=['GET', 'POST'])
def vote_admin():
    form = VoteAdminForm()
    voting_session = VotingSession.query.order_by(VotingSession.id.desc()).first()
    if form.validate_on_submit():

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

        res_left = len([k for k,v in all_votes_dict.items() if v=='left'])
        res_right = len([k for k,v in all_votes_dict.items() if v=='right'])
        results_data = {
            'left': res_left,
            'right': res_right
        }
        progess_max = max(20, max(res_left,res_right))
        progress_data = {
            'total_max': progess_max,
            'left_pcnt': int(res_left*100/progess_max),
            'right_pcnt': int(res_right*100/progess_max),
        }
    else:
        results_data = None
    return render_template('voting/admin.html', form=form, results_data=results_data, progress_data=progress_data)


@app.route('/vote/admin/data.csv')
def vote_data():
    import pandas as pd
    from salty_tickets.database import engine
    voting_sessions_df = pd.read_sql_query(VotingSession.query.statement, engine)
    votes_df = pd.read_sql_query(Vote.query.statement, engine)

    start_date = pd.datetime.today().date() - pd.DateOffset(days=2)
    voting_sessions_df = voting_sessions_df[voting_sessions_df.end_timestamp > start_date]
    votes_start = voting_sessions_df.start_timestamp.iloc[0]
    votes_df = votes_df[votes_df.vote_timestamp >= votes_start]

    votes_df['session_id'] = None
    for ix, voting_session in voting_sessions_df.iterrows():
        votes_mask = votes_df.vote_timestamp.between(voting_session.start_timestamp, voting_session.end_timestamp)
        votes_df.session_id[votes_mask] = voting_session.id

    voting_sessions_df.index = voting_sessions_df.id
    voting_sessions_df.drop('id', axis=1, inplace=True)
    votes_df = votes_df.join(voting_sessions_df, on='session_id', how='inner')

    vote_options = votes_df.vote.unique()
    for vote_option in vote_options:
        votes_df[vote_option] = None

    for ix, vote in votes_df.iterrows():
        query_votes = votes_df[votes_df.vote_timestamp.between(vote.start_timestamp, vote.vote_timestamp)]
        grouped = query_votes.groupby('voter_id').last()

        for vote_option in vote_options:
            votes_df.loc[ix, vote_option] = grouped.vote[grouped.vote == vote_option].count()

    data_csv = votes_df.to_csv(index=False)
    return Response(
        data_csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=data.csv"})


@app.template_filter('price')
def price_filter(amount):
    return '£{:.2f}'.format(amount)

@app.template_filter('price_int')
def price_int_filter(amount):
    return '£{:.0f}'.format(amount)
