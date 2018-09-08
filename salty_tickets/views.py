from flask import render_template
from flask import url_for
from salty_tickets import app
from salty_tickets import config
from salty_tickets.dao import TicketsDAO
from salty_tickets.forms import create_event_form
from salty_tickets.registration_process import do_price, do_checkout, do_pay
from salty_tickets.to_delete.sql_models import Event
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


@app.route('/register/price/<string:event_key>', methods=['POST'])
def register_get_price(event_key):
    dao = TicketsDAO()
    return do_price(dao, event_key)


@app.route('/register/checkout/<string:event_key>', methods=['POST'])
def register_checkout(event_key):
    dao = TicketsDAO()
    return do_checkout(dao, event_key)


@app.route('/register/pay/', methods=['POST'])
def register_pay():
    dao = TicketsDAO()
    return do_pay(dao)


@app.route('/register/<string:event_key>', methods=['GET'])
def register_form(event_key):
    dao = TicketsDAO()
    event = dao.get_event_by_key(event_key)
    if not event:
        return redirect(url_for('register_index'))

    form = create_event_form(event)()

    return render_template(f'events/{event_key}/signup_vue.html', event=event, form=form, config=config)


