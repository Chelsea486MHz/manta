![Manta logo](logo.png)

# Safely sign files using GPG within CI/CD pipelines

Manta is a Flask microservice that allows users to sign files using GPG without giving them access to the private key. Manta signs, the user gets the file back.

# Security features

- Token-based authentication

- MFA with [WebAuthn](https://webauthn.guide/)

- Integration with [Hashicorp Vault](https://www.vaultproject.io/)

- Metrics and alerting with [Prometheus](https://prometheus.io/)

# Installation

To run locally, use docker-compose:

`$ docker compose up -d`

The service is now reachable over port 8000.

# Run for development purposes

The service requires a Hashicorp Vault and MySQL database to be reachable. Specify the host information in `config.py` to properly connect. Alternatively, you can set the appropriate environment variables.

```
VAULT_HOST = os.environ.get('VAULT_HOST', 'localhost')
VAULT_PORT = os.environ.get('VAULT_PORT', '8200')
...
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'manta')
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'locahost')
DATABASE_USER = os.environ.get('DATABASE_USER', 'manta-user')
DATABASE_PASS = os.environ.get('DATABASE_PASS', 'manta-user-pw')
```

Set the DEBUG flag in the `Dockerfile` to `True`. Build the image and run it transiently:

`$ docker build -t manta . && docker run --rm manta`