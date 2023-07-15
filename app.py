from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics
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
gpg_notfound = metrics.counter("gpg_notfound", "Total number of requests that failed to find a GPG private key")
gpg_cantimport = metrics.counter("gpg_cantimport", "Total number of requests that failed to import the GPG private key")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
db = SQLAlchemy(app)

# GPG configuration
gpg = gnupg.GPG()

# Vault configuration
vault_client = hvac.Client(url=config.VAULT_URI)


# Represents the entries in the database
class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(48), unique=True, nullable=False)


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

    # Hash the authorization token
    hashed_token = hashlib.sha256(token.encode()).hexdigest()

    # Validate the hashed authorization token against the database
    if not Token.query.filter_by(token=hashed_token).first():
        bad_token.inc()
        return 'Unauthorized', 401

    # Save the file in tmpfs
    file = request.files['file']
    temp_file = os.path.join('/tmp', str(uuid.uuid4()))
    file.save(temp_file)

    # Connect to Hashicorp Vault using the token from the request
    vault_client.token = token

    # Retrieve the GPG private key from Hashicorp Vault
    secret = vault_client.read(config.VAULT_SECRET_PATH)
    if not secret or 'data' not in secret:
        gpg_notfound.inc()
        return 'Failed to retrieve Vault secret', 500

    # Get the GPG private key from the retrieved secret data
    gpg_private = secret['data'].get('gpg_private')
    if not gpg_private:
        gpg_notfound.inc()
        return 'GPG private key not found in the retrieved secret', 500

    # Import the GPG private key key
    imported_key = gpg.import_keys(gpg_private)
    if not imported_key.results or not imported_key.results[0].get('fingerprint'):
        gpg_cantimport.inc()
        return 'Failed to import GPG private key key', 500

    # Get the fingerprint of the imported key
    key_fingerprint = imported_key.results[0]['fingerprint']

    # Sign the file using the GPG key
    signed_data = None
    with open(temp_file, 'rb') as f:
        signed_data = gpg.sign_file(f, detach=True)

    # Delete the imported GPG key
    gpg.delete_keys(key_fingerprint)

    # Clean up the temporary file
    with open(temp_file, "ba+") as target:
        size = target.tell()
    with open(temp_file, "br+") as target:
        for i in range (3) # Number of shred passes
            target.seek(0)
            target.write(os.urandom(size))
    os.remove(temp_file)

    # Return the signed data to the client
    return signed_data.data


if __name__ == '__main__':
    app.run(os.environ.get('DEBUG', False))
