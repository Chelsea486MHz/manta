from flask import Flask, request, send_file
from flask_sqlalchemy import SQLAlchemy
import gnupg
import config
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
db = SQLAlchemy(app)

# GPG configuration
gpg = gnupg.GPG()


# Represents the entries in the database
class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)


@app.route('/sign', methods=['POST'])
def sign_file():
    # Check if the file is included in the request
    if 'file' not in request.files:
        return 'No file found', 400

    # Check if the authorization token is included in the request headers
    token = request.headers.get('Authorization')
    if not token:
        return 'Unauthorized', 401

    # Validate the authorization token against the database
    if not Token.query.filter_by(token=token).first():
        return 'Unauthorized', 401

    file = request.files['file']

    # Save the file to a temporary location
    temp_file = '/tmp/temp_file.txt'
    file.save(temp_file)

    # Sign the file using the GPG key
    signed_file = '/tmp/signed_file.txt'
    with open(temp_file, 'rb') as f:
        signed_data = gpg.sign_file(f, detach=True)
    with open(signed_file, 'wb') as f:
        f.write(signed_data.data)

    # Return the signed file to the client
    return send_file(signed_file, as_attachment=True)


if __name__ == '__main__':
    app.run(os.environ.get('DEBUG', False))
