from flask_wtf import FlaskForm
from salty_tickets.constants import LEADER, FOLLOWER
from salty_tickets.models.registrations import Person
from wtforms.fields import Field, StringField, SubmitField, SelectField, BooleanField, FormField, HiddenField, TextAreaField, RadioField
from wtforms.validators import Email, DataRequired, ValidationError


class RawField(Field):
    """
    Fictional field that retrieves any raw data
    """
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]

    def _value(self):
        return self.data


class SignupForm(FlaskForm):
    stripe_token = HiddenField()
    name = StringField(u'Your name', validators=[DataRequired()])
    email = StringField(u'Email', validators=[Email(), DataRequired()])
    location = RawField(u'Location')
    comment = TextAreaField('Comment')


class StripeCheckoutForm(FlaskForm):
    stripe_token = HiddenField(validators=[DataRequired()])
    payment_id = HiddenField()


class PartnerTokenCheck(FlaskForm):
    partner_token = StringField(validators=[DataRequired()])
    event_key = StringField(validators=[DataRequired()])


class CreateRegistrationGroupForm(FlaskForm):
    name = StringField(u'Group name', validators=[DataRequired()])
    email = StringField(u'Admin Email', validators=[Email(), DataRequired()])
    location = RawField(u'Location', validators=[DataRequired()])
    comment = TextAreaField('Comment')


class FormWithTickets:
    ticket_keys = []

    def get_item_by_key(self, ticket_key):
        return getattr(self, ticket_key)


def need_partner_check(event, event_form, form_field):
    if not form_field.data:
        for key, ticket in event.tickets.items():
            if ticket.needs_partner(event_form):
                raise ValidationError('Partner details are required')


class DanceSignupForm(FormWithTickets, SignupForm):
    dance_role = SelectField('Your Dance Role in Couple',
                             choices=[(LEADER, 'Leader'), (FOLLOWER, 'Follower'), ('', 'None')],
                             default='')
    generic_discount_code = StringField('Discount/Group code')
    partner_name = StringField(u'Partner\'s name')
    partner_email = StringField(u'Partner\'s email')
    partner_location = RawField('Partner Location')
    registration_token = StringField('Registration Code')
    partner_token = StringField('Registration Code')
    pay_all = BooleanField(default="checked")


def create_event_form(event):
    def need_partner_validator(event_form, form_field):
        return need_partner_check(event, event_form, form_field)

    class EventForm(DanceSignupForm):
        dance_role = SelectField('Your Dance Role in Couple',
                                 choices=[(LEADER, 'Leader'), (FOLLOWER, 'Follower'), ('', 'None')],
                                 default='', validators=[need_partner_validator])
        partner_name = StringField(u'Partner\'s name', validators=[need_partner_validator])
        partner_email = StringField(u'Partner\'s email', validators=[need_partner_validator])

    for ticket_key, ticket in event.tickets.items():
        setattr(EventForm, ticket_key, FormField(ticket.get_form_class()))

    for product_key, product in event.products.items():
        setattr(EventForm, product_key, FormField(product.get_form_class()))

    for discount_key, discount in event.discount_products.items():
        setattr(EventForm, discount_key, FormField(discount.get_form_class()))

    return EventForm


def get_primary_personal_info_from_form(form) -> Person:
    if hasattr(form, 'primary_person_info'):
        return form.primary_person_info
    else:
        person = Person(
            full_name=form.name.data,
            email=form.email.data,
            comment=form.comment.data,
            location=form.location.data or {},
        )
        form.primary_person_info = person
        return person


def get_partner_personal_info_from_form(form) -> Person:
    if hasattr(form, 'partner_person_info'):
        return form.partner_person_info
    else:
        person = Person(
            full_name=form.partner_name.data,
            email=form.partner_email.data,
            comment=form.comment.data,
            location=form.partner_location.data or {},
        )
        form.partner_person_info = person
        return person


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
