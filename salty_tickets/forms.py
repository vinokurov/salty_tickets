from flask_wtf import FlaskForm
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE
from salty_tickets.models.event import Event
from salty_tickets.models.personal_info import PersonalInfo
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, \
    HiddenField, TextAreaField, RadioField
from wtforms.validators import Email, DataRequired, ValidationError, Optional
from wtforms import Form as NoCsrfForm
# from salty_tickets.sql_models import Event, Registration, DANCE_ROLE_LEADER, DANCE_ROLE_FOLLOWER
# from salty_tickets.products import get_product_by_model


class SignupForm(FlaskForm):
    stripe_token = HiddenField()
    name = StringField(u'Your name', validators=[DataRequired()])
    email = StringField(u'Email', validators=[Email(), DataRequired()])
    comment = TextAreaField('Comment')
    # submit = SubmitField(u'Signup')


class FormWithProducts:
    product_keys = []

    def get_product_by_key(self, product_key):
        return getattr(self, product_key)


def need_partner_check(form, field):
    for key in form.product_keys:
        product_form = form.get_product_by_key(key)
        needs_partner = product_form.needs_partner()
        if needs_partner and not field.data:
            raise ValidationError('Partner details are required')


class DanceSignupForm(FormWithProducts, SignupForm):
    location_query = StringField('Location')
    country = StringField('Country')
    state = StringField('State')
    city = StringField('City')
    dance_role = SelectField('Your Dance Role in Couple',
                             choices=[(LEADER, 'Leader'), (FOLLOWER, 'Follower')],
                             default=LEADER)
    partner_name = StringField(u'Partner\'s name', validators=[need_partner_check])
    partner_email = StringField(u'Partner\'s email', validators=[need_partner_check])
    partner_location_query = StringField('Partner\'s Location')
    partner_country = StringField('Partner\'s Country')
    partner_state = StringField('Partner\'s State')
    partner_city = StringField('Partner\'s City')
    registration_token = StringField('Registration Code')


def create_event_form(event):
    class EventForm(DanceSignupForm):
        pass

    for product_key, product in event.products.items():
        setattr(EventForm, product_key, FormField(product.get_form_class()))

    return EventForm


def get_registration_from_form(form):
    from salty_tickets.sql_models import Event, Registration
    assert isinstance(form, SignupForm)
    registration_model = Registration(
        name=form.name.data,
        email=form.email.data,
        comment=form.comment.data,
        country=form.country.data,
        state=form.state.data,
        city=form.city.data
    )
    return registration_model


def get_partner_registration_from_form(form):
    from salty_tickets.sql_models import Event, Registration
    assert isinstance(form, SignupForm)
    registration_model = Registration(
        name=form.partner_name.data,
        email=form.partner_email.data,
        comment=form.comment.data,
        country=form.partner_country.data,
        state=form.partner_state.data,
        city=form.partner_city.data
    )
    return registration_model


def get_primary_personal_info_from_form(form):
    return PersonalInfo(
        full_name=form.name.data,
        email=form.email.data,
        comment=form.comment.data,
        # location=form.location,
    )


def get_partner_personal_info_from_form(form):
    return PersonalInfo(
        full_name=form.partner_name.data,
        email=form.partner_email.data,
        comment=form.comment.data,
        # location=form.partner_location,
    )


class OrderProductCancelForm(FlaskForm):
    confirm = BooleanField('I confirm I want to cancel', validators=[DataRequired()])
    comment = TextAreaField('Reason to cancel')
    submit = SubmitField('Cancel my participation')


class RemainingPaymentForm(FlaskForm):
    stripe_token = HiddenField()
    amount = HiddenField()


class VoteForm(FlaskForm):
    client_fingerprint = StringField(255)
    options = RadioField(choices=[('left', 'left'), ('right', 'right')])


class VoteAdminForm(FlaskForm):
    name = StringField('Name')
    start_voting = SubmitField('Start Voting')
    stop_voting = SubmitField('Stop Voting')
