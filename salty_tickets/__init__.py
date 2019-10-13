from config import MONGO
from flask import Flask, render_template, flash, escape
# from flask_bootstrap import Bootstrap
# from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_simplelogin import SimpleLogin
# from salty_tickets import config

__author__ = 'vnkrv'

sess = Session()
login = SimpleLogin()


def create_app():
    app = Flask('salty_tickets')
    app.config.from_object('config')
    # Bootstrap(app)
    # db = SQLAlchemy(app)
    # app.secret_key = 'devtest'

    # Session(app)
    sess.init_app(app)

    app.config['SIMPLELOGIN_USERNAME'] = 'salty'
    app.config['SIMPLELOGIN_PASSWORD'] = 'jiterrrbugHFRSJ'
    # SimpleLogin(app)
    login.init_app(app)

    with app.app_context():
        from . import views
        # from . import template_filters

        app.register_blueprint(views.tickets_bp)

        return app

app = create_app()
