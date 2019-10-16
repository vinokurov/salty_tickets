import dramatiq
from flask import Flask, render_template, flash, escape
# from flask_bootstrap import Bootstrap
# from flask_sqlalchemy import SQLAlchemy
from flask_melodramatiq import Broker
from flask_session import Session
from flask_simplelogin import SimpleLogin
# from salty_tickets import config
from salty_tickets.dao import TicketsDAO

__author__ = 'vnkrv'

sess = Session()
login = SimpleLogin()

print('registering broker')
broker = Broker()
dramatiq.set_broker(broker)

def create_app():
    app = Flask('salty_tickets')
    app.config.from_object('config')
    # Bootstrap(app)
    # db = SQLAlchemy(app)
    # app.secret_key = 'devtest'

    # Session(app)
    sess.init_app(app)

    app.config['SERVER_NAME'] = 'localhost'

    app.config['SIMPLELOGIN_USERNAME'] = 'salty'
    app.config['SIMPLELOGIN_PASSWORD'] = 'jiterrrbugHFRSJ'
    # SimpleLogin(app)
    login.init_app(app)

    with app.app_context():
        from . import views
        # from . import template_filters
        app.config['dao'] = TicketsDAO(app.config['MONGO'])

        app.register_blueprint(views.tickets_bp)

        # from salty_tickets.tasks import broker
        broker.init_app(app)


        return app

# app = create_app()
