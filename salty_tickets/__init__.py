from flask import Flask, render_template, flash, escape
# from flask_bootstrap import Bootstrap
# from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_simplelogin import SimpleLogin
# from salty_tickets import config

__author__ = 'vnkrv'

app = Flask('salty_tickets')
app.config.from_object('config')
# Bootstrap(app)
# db = SQLAlchemy(app)
# app.secret_key = 'devtest'
Session(app)
app.config['SIMPLELOGIN_USERNAME'] = 'salty'
app.config['SIMPLELOGIN_PASSWORD'] = 'jiterrrbugQ!2w'
SimpleLogin(app)

from salty_tickets import views
from salty_tickets import template_filters
