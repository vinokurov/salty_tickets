from flask import url_for, jsonify
from werkzeug.utils import redirect

from .database import db_session
from .forms import create_event_form
from .pricing_rules import get_salty_recipes_price, get_order_for_event
from .models import Event
from flask import Flask, render_template, flash, escape
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
__author__ = 'vnkrv'


app = Flask('salty')
Bootstrap(app)
db = SQLAlchemy(app)
app.secret_key = 'devtest'


@app.route('/')
def index():
    # return render_template('index.html')
    event = Event.query.filter_by(active=True).order_by(Event.start_date).first()
    if event:
        return redirect(url_for('example_form', event_key=event.event_key))


@app.route('/register/<string:event_key>', methods=('GET', 'POST'))
def example_form(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    print(event.name)
    form = create_event_form(event)()
    # form = SaltyRecipesSignupForm()

    if form.validate_on_submit():
        return 'your total price: £{}'.format(get_salty_recipes_price(form))

    return render_template('signup.html', event=event, form=form)


@app.route('/register/total_price/<string:event_key>', methods=('POST',))
def total_price(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_event_form(event)()
    print('Starting calculate total price for event {}'.format(event.name))
    if form.validate_on_submit():
        user_order = get_order_for_event(event, form)
        price = user_order.total_price
        print(price)
        return jsonify({'total_price': price, 'order_summary_html': render_template('order_summary.html', order=user_order, price=price)})
    else:
        return jsonify({})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
