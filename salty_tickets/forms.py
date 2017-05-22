from flask_wtf import Form
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, HiddenField, TextAreaField
from wtforms.validators import Email, DataRequired
from wtforms import Form as NoCsrfForm
from .models import Event
from .products import get_product_by_model


class SignupForm(Form):
    stripe_token = HiddenField()
    name = StringField(u'Your name', validators=[DataRequired()])
    email = StringField(u'Email', validators=[Email(), DataRequired()])
    comment = TextAreaField('Comment')
    # submit = SubmitField(u'Signup')


class CrowdfundingSignupForm(SignupForm):
    show_comment = BooleanField(label='Show comment', default=True)
    show_contribution = BooleanField(label='Show contribution', default=True)


def create_event_form(event):
    assert (isinstance(event, Event))

    class EventForm(SignupForm):
        product_keys = []

        def get_product_by_key(self, product_key):
            return getattr(self, product_key)

    product_keys = []
    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_key = product_model.product_key
        setattr(EventForm, product_key, FormField(product.get_form()))
        product_keys.append(product_key)
    setattr(EventForm, 'product_keys', product_keys)
    return EventForm


def create_crowdfunding_form(event):
    assert (isinstance(event, Event))

    class EventForm(CrowdfundingSignupForm):
        product_keys = []

        def get_product_by_key(self, product_key):
            return getattr(self, product_key)

    product_keys = []
    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_key = product_model.product_key
        setattr(EventForm, product_key, FormField(product.get_form()))
        product_keys.append(product_key)
    setattr(EventForm, 'product_keys', product_keys)
    return EventForm
