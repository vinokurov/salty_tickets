import pymongo

STRIPE_SK = 'sk_test_NEwiOsRtQbOCgjglKtiJN5R4'
STRIPE_PK = 'pk_test_JINxJqXoY58hgW37stGd09hK'

MODE_TESTING = STRIPE_SK.find('live') is -1 and STRIPE_PK.find('live') is -1

DATABASE_USERNAME = ''
DATABASE_PASSWORD = ''
DATABASE_HOSTNAME = ''
DATABASE_DBNAME = ''

SECRET_KEY = 'devtest'
SALT_EMAIL = ''
SALT_ORDER_PRODUCT = ''
SALT_ORDER = ''
SALT_GROUP_TOKEN = ''
SALT_PARTNER_TOKEN = ''
SALT_REGISTRATION_TOKEN = ''
EMAIL_FROM = ''

MONGO = 'mongodb://localhost/salty_tickets'

SESSION_TYPE = 'mongodb'
SESSION_MONGODB = pymongo.MongoClient('mongodb://localhost')
SESSION_MONGODB_DB = 'salty_tickets'

