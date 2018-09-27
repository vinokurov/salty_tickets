from flask_wtf import FlaskForm
from salty_tickets.constants import LEADER, FOLLOWER
from salty_tickets.models.registrations import PersonInfo
from wtforms.fields import StringField, SubmitField, SelectField, BooleanField, FormField, HiddenField, TextAreaField, RadioField
from wtforms.validators import Email, DataRequired, ValidationError


class SignupForm(FlaskForm):
    stripe_token = HiddenField()
    name = StringField(u'Your name', validators=[DataRequired()])
    email = StringField(u'Email', validators=[Email(), DataRequired()])
    comment = TextAreaField('Comment')
    # submit = SubmitField(u'Signup')


class StripeCheckoutForm(FlaskForm):
    stripe_token = HiddenField(validators=[DataRequired()])
    payment_id = HiddenField()


class PartnerTokenCheck(FlaskForm):
    partner_token = StringField(validators=[DataRequired()])
    event_key = StringField(validators=[DataRequired()])


class FormWithProducts:
    product_keys = []

    def get_product_by_key(self, product_key):
        return getattr(self, product_key)


def need_partner_check(event, event_form, form_field):
    if not form_field.data:
        for key, product in event.products.items():
            if product.needs_partner(event_form):
                raise ValidationError('Partner details are required')


class DanceSignupForm(FormWithProducts, SignupForm):
    location_query = StringField('Location')
    country = StringField('Country')
    state = StringField('State')
    city = StringField('City')
    dance_role = SelectField('Your Dance Role in Couple',
                             choices=[(LEADER, 'Leader'), (FOLLOWER, 'Follower'), ('', 'None')],
                             default='')
    partner_name = StringField(u'Partner\'s name')
    partner_email = StringField(u'Partner\'s email')
    partner_location_query = StringField('Partner\'s Location')
    partner_country = StringField('Partner\'s Country')
    partner_state = StringField('Partner\'s State')
    partner_city = StringField('Partner\'s City')
    registration_token = StringField('Registration Code')
    partner_token = StringField('Registration Code')


def create_event_form(event):
    def need_partner_validator(event_form, form_field):
        return need_partner_check(event, event_form, form_field)

    class EventForm(DanceSignupForm):
        dance_role = SelectField('Your Dance Role in Couple',
                                 choices=[(LEADER, 'Leader'), (FOLLOWER, 'Follower'), ('', 'None')],
                                 default='', validators=[need_partner_validator])
        partner_name = StringField(u'Partner\'s name', validators=[need_partner_validator])
        partner_email = StringField(u'Partner\'s email', validators=[need_partner_validator])

    for product_key, product in event.products.items():
        setattr(EventForm, product_key, FormField(product.get_form_class()))

    return EventForm


def get_registration_from_form(form):
    from salty_tickets.to_delete.sql_models import Registration
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
    from salty_tickets.to_delete.sql_models import Registration
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
    return PersonInfo(
        full_name=form.name.data,
        email=form.email.data,
        comment=form.comment.data,
        # location=form.location,
    )


def get_partner_personal_info_from_form(form):
    return PersonInfo(
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
