from flask import Flask, render_template, flash, escape
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
# from salty_tickets import config

__author__ = 'vnkrv'

app = Flask('salty')
Bootstrap(app)
db = SQLAlchemy(app)
app.secret_key = 'devtest'

# from salty_tickets import views