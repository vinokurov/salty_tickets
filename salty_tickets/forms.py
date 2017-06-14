from flask_wtf import FlaskForm
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, HiddenField, TextAreaField
from wtforms.validators import Email, DataRequired, ValidationError, Optional
from wtforms import Form as NoCsrfForm
from salty_tickets.models import Event, Registration
from salty_tickets.products import get_product_by_model


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
        # if needs_partner:
            raise ValidationError('Partner details are required')


class DanceSignupForm(SignupForm, FormWithProducts):
    partner_name = StringField(u'Partner\'s name', validators=[need_partner_check])
    partner_email = StringField(u'Partner\'s email', validators=[need_partner_check])



class CrowdfundingSignupForm(SignupForm, FormWithProducts):
    anonymous = BooleanField(label='Contribute anonymously', default=False)


def create_event_form(event):
    assert (isinstance(event, Event))

    class EventForm(DanceSignupForm):
        pass

    product_keys = []
    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_key = product_model.product_key
        setattr(EventForm, product_key, FormField(product.get_form(product_model=product_model)))
        product_keys.append(product_key)
    setattr(EventForm, 'product_keys', product_keys)
    return EventForm


def create_crowdfunding_form(event):
    assert (isinstance(event, Event))

    class EventForm(CrowdfundingSignupForm):
        pass

    product_keys = []
    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_key = product_model.product_key
        setattr(EventForm, product_key, FormField(product.get_form(product_model=product_model)))
        product_keys.append(product_key)
    setattr(EventForm, 'product_keys', product_keys)
    return EventForm


def get_registration_from_form(form):
    assert isinstance(form, SignupForm)
    registration_model = Registration(
        name=form.name.data,
        email=form.email.data,
        comment=form.comment.data
    )
    return registration_model


def get_partner_registration_from_form(form):
    assert isinstance(form, SignupForm)
    registration_model = Registration(
        name=form.partner_name.data,
        email=form.partner_email.data,
        comment=form.comment.data
    )
    return registration_model

