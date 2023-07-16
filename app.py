from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics
from cryptography.fernet import Fernet
import tempfile
import gnupg
import config
import os
import hashlib
import hvac
import uuid

app = Flask(__name__)

# Prometheus configuration
metrics = PrometheusMetrics(app)
metrics.info("app_info", "Application Information", version="1.0.0")

# Define metrics
requests = metrics.counter("requests", "Total number of requests")
no_file = metrics.counter("no_file", "Total number of requests without file")
no_token = metrics.counter("no_token", "Total number of requests without token")
bad_token = metrics.counter("bad_token", "Total number of requests with unauthorized token")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
db = SQLAlchemy(app)

# Vault configuration
vault_client = hvac.Client(url=config.VAULT_URI)


# Represents the entries in the database
class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(48), unique=True, nullable=False)
    token_vault = db.Column(db.String(512), nullable=False)


@app.route('/sign', methods=['POST'])
def sign_file():
    requests.inc()

    # Check if the file is included in the request
    if 'file' not in request.files:
        no_file.inc()
        return 'No file found', 400

    # Check if the authorization token is included in the request headers
    token = request.headers.get('Authorization')
    if not token:
        no_token.inc()
        return 'Unauthorized', 401

    # Validate the hashed authorization token against the database
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    if not Token.query.filter_by(token=hashed_token).first():
        bad_token.inc()
        return 'Unauthorized', 401

    # Save the file in tmpfs
    file = request.files['file']
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, str(uuid.uuid4()))
    file.save(temp_file)

    # Decrypt the token_vault column using the authentication token as the decryption secret
    fernet = Fernet(token.encode())
    token_vault_encrypted = Token.query.filter_by(token=hashed_token).first()
    token_vault_decrypted = fernet.decrypt(token_vault_encrypted.token_vault.encode()).decode()

    # Connect to Hashicorp Vault using the decrypted token
    vault_client.token = token_vault_decrypted

    # Get the GPG private key from the Hashicorp Vault
    secret = vault_client.read(config.VAULT_SECRET_PATH)
    gpg_private = secret['data'].get('gpg_private')

    # Import the GPG private key
    gpg = gnupg.GPG(gnupghome=temp_dir)
    imported_key = gpg.import_keys(gpg_private)

    # Sign the file using the GPG key
    signed_data = None
    with open(temp_file, 'rb') as f:
        signed_data = gpg.sign_file(f, detach=True)

    # Delete the imported GPG key
    key_fingerprint = imported_key.results[0]['fingerprint']
    gpg.delete_keys(key_fingerprint)

    # Clean up the temporary file
    with open(temp_file, "ba+") as target:
        size = target.tell()
    with open(temp_file, "br+") as target:
        for i in range(3):  # Number of shred passes
            target.seek(0)
            target.write(os.urandom(size))
    os.remove(temp_file)
    os.rmdir(temp_dir)

    # Return the signed data to the client
    return signed_data.data


if __name__ == '__main__':
    app.run(os.environ.get('DEBUG', False))
