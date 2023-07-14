VAULT_SECRET_PATH = 'secret/gpg-keys'
VAULT_HOST = 'localhost'
VAULT_PORT = '8200'

VAULT_URI = 'http://' + VAULT_HOST + ':' + VAULT_PORT

DATABASE_NAME = 'manta'
DATABASE_HOST = 'localhost'
DATABASE_USER = 'manta-user'
DATABASE_PASS = 'manta-user-pw'

DATABASE_URI = 'mysql+pymysql://' + DATABASE_USER + ':' + DATABASE_PASS + '@' + DATABASE_HOST + '/' + DATABASE_NAME
