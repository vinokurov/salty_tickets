from flask import render_template, redirect, url_for, request, make_response, jsonify
from flask_simplelogin import login_required
from flask_wtf import FlaskForm
# from salty.rating.admin import start_contest, stop_contest, get_contest_results
# from salty.rating.voting import generate_voter_uid, add_rating_vote, get_current_contest_config, get_my_last_vote
from salty_tickets import app
from salty_tickets import config
from salty_tickets.actions.mailing_lists import do_email_unsubscribe
from salty_tickets.api.admin import do_get_event_stats
from salty_tickets.config import MONGO
from salty_tickets.dao import TicketsDAO
from salty_tickets.api.registration_process import do_price, do_checkout, do_pay, do_get_payment_status, \
    do_check_partner_token, EventInfo, balance_event_waiting_lists, do_validate_discount_code_token, \
    do_validate_registration_group_token, do_create_registration_group, do_get_prior_registrations
from salty_tickets.api.user_order import do_get_user_order_info
from salty_tickets.models.registrations import Payment
from salty_tickets.tokens import PaymentId
from salty_tickets.utils.utils import jsonify_dataclass
from werkzeug.exceptions import abort

__author__ = 'vnkrv'


# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def catch_all(path):
#     return 'Temporary unavailable'
#
# """


if app.debug:
    @app.route('/static/dist/rating/<path:path>')
    def catch_all(path):
        import requests
        return requests.get('http://localhost:8080/{}'.format(path)).text


@app.route('/register')
@app.route('/register/')
def register_index():
    return redirect(url_for('event_index', event_key='mind_the_shag_2019'))


@app.route('/register/<string:event_key>', methods=['GET'])
def event_index(event_key):
    dao = TicketsDAO(MONGO)
    event = dao.get_event_by_key(event_key, get_registrations=False)
    if event is None:
        abort(404)
    form = FlaskForm()
    reg_token = request.args.get('reg_token', default='')
    return render_template("event.html", event=event, form=form, stripe_pk=config.STRIPE_PK, reg_token=reg_token)


@app.route('/event/<string:event_key>', methods=['GET', 'OPTIONS'])
def register_event_details(event_key):
    dao = TicketsDAO(MONGO)
    event = dao.get_event_by_key(event_key, get_registrations=True)
    if event is None:
        abort(404)
    return jsonify_dataclass(EventInfo.from_event(event))


@app.route('/price/<string:event_key>', methods=['GET', 'POST'])
def register_get_price(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_price(dao, event_key))


@app.route('/checkout/<string:event_key>', methods=['POST'])
def register_checkout(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_checkout(dao, event_key))


@app.route('/pay/', methods=['POST'])
def register_pay():
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_pay(dao))


@app.route('/payment_status', methods=['POST'])
def payment_status():
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_get_payment_status(dao))


@app.route('/check_partner_token', methods=['POST'])
def check_partner_token():
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_check_partner_token(dao))


@app.route('/order/<string:pmt_token>', methods=['GET'])
def user_order_index(pmt_token):
    return render_template("user_order.html", pmt_token=pmt_token, stripe_pk=config.STRIPE_PK)


@app.route('/order_info/<string:pmt_token>', methods=['POST', 'GET'])
def user_order_info(pmt_token):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_get_user_order_info(dao, pmt_token))


@app.route('/check_discount_token/<string:event_key>', methods=['POST'])
def check_discount_token(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_validate_discount_code_token(dao, event_key))


@app.route('/check_registration_group_token/<string:event_key>', methods=['POST'])
def check_registration_group_token(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_validate_registration_group_token(dao, event_key))


@app.route('/create_registration_group/<string:event_key>', methods=['POST'])
def create_registration_group(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_create_registration_group(dao, event_key))


@app.route('/prior_registrations/<string:event_key>', methods=['POST'])
def prior_registrations(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_get_prior_registrations(dao, event_key))


@app.route('/unsubscribe_email/<string:reg_token>', methods=['GET'])
def unsubscribe_email(reg_token):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_email_unsubscribe(dao, reg_token))


#####################################################################
#########                A D M I N                   ################
#####################################################################


@app.route('/admin/event/<string:event_key>', methods=['GET'])
@login_required
def admin_event_index(event_key):
    return render_template('admin_event.html', event_key=event_key)


@app.route('/admin/event_info/<string:event_key>', methods=['GET'])
@login_required
def admin_event_info(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_get_event_stats(dao, event_key))


@app.route('/admin/order/<string:payment_id>', methods=['GET'])
@login_required
def admin_order(payment_id):
    payment = Payment(paid_by=None)
    payment.id = payment_id
    pmt_token = PaymentId().serialize(payment)
    return redirect(url_for('user_order_index', pmt_token=pmt_token))


@app.route('/admin/balance_event/<string:event_key>', methods=['GET'])
@login_required
def admin_balance_event(event_key):
    dao = TicketsDAO(MONGO)
    balance_event_waiting_lists(dao, event_key)
    return ''

#####################################################################
#########             R A T I N G                    ################
#####################################################################


COOKIE_RATING_VOTER_UID = 'voter_uid'
COOKIE_RATING_IS_JUDGE = 'jj'


def rating_vote_response():
    resp = make_response(render_template('rating/vote.html'))
    voter_uid = request.cookies.get(COOKIE_RATING_VOTER_UID)
    if not voter_uid:
        resp.set_cookie(COOKIE_RATING_VOTER_UID, generate_voter_uid())
    return resp


@app.route('/')
@app.route('/r')
@app.route('/rating', methods=['GET'])
def rating_vote():
    resp = rating_vote_response()
    resp.set_cookie(COOKIE_RATING_IS_JUDGE, '')
    return resp


@app.route('/rating_judge', methods=['GET'])
def rating_vote_judge():
    resp = rating_vote_response()
    resp.set_cookie(COOKIE_RATING_IS_JUDGE, 'true')
    return resp


@app.route('/rating/vote/submit', methods=['POST'])
def rating_judge_submit():
    voter_uid = request.cookies.get(COOKIE_RATING_VOTER_UID)
    if voter_uid:
        is_judge = request.cookies.get(COOKIE_RATING_IS_JUDGE, False)
        add_rating_vote(request.json, voter_uid, is_judge=is_judge)
    return jsonify({})


@app.route('/rating/contest', methods=['GET'])
def rating_get_contest_config():
    return jsonify(get_current_contest_config(active_only=True))


@app.route('/rating/contest_any', methods=['GET'])
def rating_get_contest_config_any():
    return jsonify(get_current_contest_config(active_only=False))


@app.route('/rating/my_vote', methods=['POST'])
def rating_get_my_last_vote():
    voter_uid = request.cookies.get(COOKIE_RATING_VOTER_UID)
    if voter_uid:
        return jsonify(get_my_last_vote(request.json.get('contest_uid'), voter_uid))
    return jsonify({})


@app.route('/rating/admin', methods=['GET'])
def rating_admin():
    return render_template('rating/admin.html')


@app.route('/rating/admin/new', methods=['POST'])
def rating_admin_new_contest():
    return jsonify(start_contest(request.json))


@app.route('/rating/admin/stop', methods=['POST'])
def rating_admin_stop_contest():
    contest_config = stop_contest(request.json)
    return jsonify(get_contest_results(contest_config))


@app.route('/rating/admin/results', methods=['POST'])
def rating_admin_contest_results():
    return jsonify(get_contest_results(request.json))
