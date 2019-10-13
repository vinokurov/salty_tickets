import pymongo

STRIPE_SK = 'sk_test_'
STRIPE_PK = 'pk_test_'

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
EMAIL_FROM = 'registration@saltyjitterbugs.co.uk'

MONGO = 'mongodb://localhost/salty_tickets'

SESSION_TYPE = 'mongodb'
SESSION_MONGODB = pymongo.MongoClient('mongodb://localhost')
SESSION_MONGODB_DB = 'salty_tickets'

