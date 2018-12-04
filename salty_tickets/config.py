
STRIPE_SK = 'sk_test_AAA'
STRIPE_PK = 'pk_test_AAA'

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

MAILGUN_KEY = 'key-AAA'

EMAIL_FROM = 'Salty Jitterbugs <registration@saltyjitterbugs.co.uk>'
EMAIL_DEBUG = 'info@saltyjitterbugs.co.uk'

MONGO = 'mongodb://localhost/salty_tickets'

SESSION_TYPE = 'mongodb'
SESSION_MONGODB = 'mongodb://localhost'

