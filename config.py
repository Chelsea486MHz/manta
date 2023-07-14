VAULT_SECRET_PATH = 'secret/gpg-keys'
VAULT_HOST = os.environ.get('VAULT_HOST', 'localhost')
VAULT_PORT = os.environ.get('VAULT_PORT', '8200')

VAULT_URI = 'http://' + VAULT_HOST + ':' + VAULT_PORT

DATABASE_NAME = os.environ.get('DATABASE_NAME', 'manta')
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'locahost')
DATABASE_USER = os.environ.get('DATABASE_USER', 'manta-user')
DATABASE_PASS = os.environ.get('DATABASE_PASS', 'manta-user-pw')

DATABASE_URI = 'mysql+pymysql://' + DATABASE_USER + ':' + DATABASE_PASS + '@' + DATABASE_HOST + '/' + DATABASE_NAME
