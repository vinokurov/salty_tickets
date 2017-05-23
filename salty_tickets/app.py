from flask import url_for, jsonify
from werkzeug.utils import redirect

from .database import db_session
from .forms import create_event_form, create_crowdfunding_form, get_registration_from_form
from .pricing_rules import get_salty_recipes_price, get_order_for_event, get_total_raised, \
    get_order_for_crowdfunding_event, get_stripe_properties
from .models import Event, Order, CrowdfundingRegistrationProperties, Registration
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
    event = Event.query.filter_by(active=True, event_type='dance').order_by(Event.start_date).first()
    if event:
        return redirect(url_for('register_form', event_key=event.event_key))


@app.route('/register/<string:event_key>', methods=('GET', 'POST'))
def register_form(event_key):
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
    print(event.name)
    form = create_crowdfunding_form(event)()

    total_stats = get_total_raised(event)

    if form.validate_on_submit():
        registration = get_registration_from_form(form)
        print(registration)
        user_order = get_order_for_crowdfunding_event(event, form)
        user_order.status = 'Paid'
        registration.orders.append(user_order)
        registration.crowdfunding_registration_properties = \
            CrowdfundingRegistrationProperties(anonymous=form.anonymous.data)
        # db_session.add(registration)
        # db_session.add(event)
        event.registrations.append(registration)
        db_session.commit()
        return redirect(url_for('crowdfunding_form', event_key=event.event_key))

    print(event.id)
    print(event.registrations.count())
    contributors = event.registrations.order_by(Registration.registered_datetime.desc()).all()
    return render_template('crowdfunding.html', event=event, form=form, total_stats=total_stats, contributors=contributors)


@app.route('/crowdfunding/checkout/<string:event_key>', methods=['POST'])
def crowdfunding_checkout(event_key):
    event = Event.query.filter_by(event_key=event_key).first()
    form = create_crowdfunding_form(event)()

    redurn_dict = dict(errors={})

    if form.validate_on_submit():
        user_order = get_order_for_crowdfunding_event(event, form)
        redurn_dict['stripe'] = get_stripe_properties(event, user_order, form)
        redurn_dict['order_summary_html'] = render_template('order_summary.html', user_order=user_order)
    else:
        redurn_dict['order_summary_html'] = render_template('order_summary.html', user_order=Order(total_price=0))
        redurn_dict['errors'] = form.errors
    return jsonify(redurn_dict)


@app.route('/crowdfunding/contributors/<string:event_key>', methods=['GET'])
def crowdfunding_contributors(event_key):
    pass


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
