from flask import render_template
from flask import url_for, jsonify
from salty_tickets import app
from salty_tickets import config
from salty_tickets.database import db_session
from salty_tickets.forms import create_event_form, create_crowdfunding_form, get_registration_from_form
from salty_tickets.models import Event, Order, CrowdfundingRegistrationProperties, Registration
from salty_tickets.pricing_rules import get_salty_recipes_price, get_order_for_event, get_total_raised, \
    get_order_for_crowdfunding_event, get_stripe_properties
from werkzeug.utils import redirect

__author__ = 'vnkrv'


@app.route('/')
def index():
    return redirect(url_for('crowdfunding_index'))
    # return render_template('index.html')
    # event = Event.query.filter_by(active=True, event_type='dance').order_by(Event.start_date).first()
    # if event:
    #     return redirect(url_for('register_form', event_key=event.event_key))


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
        registration.orders.append(user_order)
        registration.crowdfunding_registration_properties = \
            CrowdfundingRegistrationProperties(anonymous=form.anonymous.data)
        event.registrations.append(registration)
        db_session.commit()
        success, response = user_order.charge(form.stripe_token.data)
        if success:
            db_session.commit()
            return redirect(url_for('crowdfunding_thankyou', event_key=event.event_key))
        else:
            return response

    print(event.id)
    print(event.registrations.count())
    contributors = event.registrations.order_by(Registration.registered_datetime.desc()).all()
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
        user_order = get_order_for_crowdfunding_event(event, form)
        return_dict['stripe'] = get_stripe_properties(event, user_order, form)
        return_dict['order_summary_html'] = render_template('order_summary.html', user_order=user_order)
    else:
        return_dict['order_summary_html'] = render_template('order_summary.html', user_order=Order(total_price=0))
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