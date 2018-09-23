from flask import Flask, render_template, flash, escape
from flask_bootstrap import Bootstrap
# from flask_sqlalchemy import SQLAlchemy
from salty_tickets import config

__author__ = 'vnkrv'

app = Flask('salty_tickets')
Bootstrap(app)
# db = SQLAlchemy(app)
app.secret_key = 'devtest'
print(app.template_folder)

from salty_tickets import views
from salty_tickets import template_filters
