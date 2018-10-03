from flask import render_template, redirect
from salty_tickets import app
from salty_tickets import config
from salty_tickets.api.admin import do_get_event_stats
from salty_tickets.config import MONGO
from salty_tickets.dao import TicketsDAO
from salty_tickets.forms import create_event_form
from salty_tickets.api.registration_process import do_price, do_checkout, do_pay, do_get_payment_status, \
    do_check_partner_token, EventInfo
from salty_tickets.api.user_order import do_get_user_order_info
from salty_tickets.utils.utils import jsonify_dataclass


__author__ = 'vnkrv'

# @app.after_request
# def add_cors_headers(response):
#     # r = request.referrer[:-1]
#     # if r in ['http://localhost:8080', 'http://localhost:9000']:
#     response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
#     response.headers.add('Access-Control-Allow-Credentials', 'true')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#     response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
#     response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
#     response.headers.add('Access-Control-Allow-Headers', 'Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
#     return response


# @app.route('/')


# import requests
# import os
# from flask import send_from_directory
#
# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def serve(path):
#     return send_from_directory('static', path)
#     # if path != "" and os.path.exists("/static/" + path):
#         # return send_from_directory('static', path)
#     # else:
#         # return "Hello"


@app.route('/r')
@app.route('/register')
@app.route('/register/')
def register_index():
    return 'Hello'


@app.route('/register/<string:event_key>', methods=['GET'])
def event_index(event_key):
    dao = TicketsDAO(MONGO)
    event = dao.get_event_by_key(event_key, get_registrations=False)
    form = create_event_form(event)()
    return render_template("event.html", event=event, form=form, stripe_pk=config.STRIPE_PK)


@app.route('/event/<string:event_key>', methods=['GET', 'OPTIONS'])
def register_event_details(event_key):
    dao = TicketsDAO(MONGO)
    event = dao.get_event_by_key(event_key, get_registrations=True)
    # print(event)
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
    dao = TicketsDAO(MONGO)
    return render_template("user_order.html", pmt_token=pmt_token, stripe_pk=config.STRIPE_PK)


@app.route('/order_info/<string:pmt_token>', methods=['POST', 'GET'])
def user_order_info(pmt_token):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_get_user_order_info(dao, pmt_token))

#####################################################################
#########                A D M I N                   ################
#####################################################################


@app.route('/admin/event/<string:event_key>', methods=['GET'])
def admin_event_index(event_key):
    return render_template('admin_event.html', event_key=event_key)


@app.route('/admin/event_info/<string:event_key>', methods=['GET'])
def admin_event_info(event_key):
    dao = TicketsDAO(MONGO)
    return jsonify_dataclass(do_get_event_stats(dao, event_key))



