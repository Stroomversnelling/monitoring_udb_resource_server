#Adapted from: https://github.com/auth0-samples/auth0-python-web-app/blob/master/01-Login/server.py
"""Python Flask WebApp Auth0 integration example
"""
from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import Unauthorized

#from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from flask import request

from authlib.flask.client import OAuth
from six.moves.urllib.parse import urlencode

from urllib.parse import urlencode

import udb.config.udb_api_config as config
import sys

from jose import JWTError, jwt
import six


#ENV_FILE = find_dotenv()
#if ENV_FILE:
#    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = "http://localhost:3000/callback"
AUTH0_CLIENT_ID = config.CLIENT_APP_ID
AUTH0_CLIENT_SECRET = config.CLIENT_APP_SECRET
AUTH0_DOMAIN = config.AUTH0_DOMAIN
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = config.API_AUDIENCE
PROFILE_KEY = 'profile'
SCOPE = 'udbserver'
JWT_PAYLOAD = 'jwt_payload'

JWT_VERIFY_DEFAULTS = {
    'verify_signature': True, 
    'verify_aud': True, 
    'verify_iat': True, 
    'verify_exp': True, 
    'verify_nbf': True, 
    'verify_iss': True, 
    'verify_sub': True, 
    'verify_jti': True, 
    'verify_at_hash': True, 
    'leeway': 0,
}

app = Flask(__name__, static_url_path='/public', static_folder='./public')

#change secret... probably the auth code PKCE related secret for authlib - will need to look at authlib docs
app.secret_key = "Not sure what this is yet."
app.debug = True

@app.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
    return response


oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + '/oauth/token',
    authorize_url=AUTH0_BASE_URL + '/authorize',
    client_kwargs={
        'scope': SCOPE,
    },
)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if JWT_PAYLOAD not in session:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated


# Controllers API
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/callback')
def callback_handling():
    token = auth0.authorize_access_token()

    #resp = auth0.get('userinfo')
    #userinfo = resp.json()

    token['token_decoded'] = decode_token(token["access_token"])

    session[JWT_PAYLOAD] = token
    #session[PROFILE_KEY] = {
    #    'user_id': userinfo['sub'],
    #    'name': userinfo['name'],
    #    'picture': userinfo['picture']
    #}
    return redirect('/dashboard')


@app.route('/login')
def login():
    pdb_url = request.args.get('pdb_url')
    if pdb_url is not None and not pdb_url == "":
        return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE, pdb_url=pdb_url)
    else:
        return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE)


@app.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@app.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html',
                           userinfo=session[JWT_PAYLOAD],
                           userinfo_pretty=json.dumps(session[JWT_PAYLOAD], indent=4))

def decode_token(token):
    print("Gonna print the token:", file=sys.stdout)
    print(jwt.get_unverified_header(token), file=sys.stdout)
    print(jwt.get_unverified_claims(token), file=sys.stdout)
    try:
        return jwt.decode(token, config.JWT_PUBLIC_KEY_SET, algorithms=[config.JWT_ALGORITHM], issuer=config.ISSUER, audience=config.API_AUDIENCE, options = JWT_VERIFY_DEFAULTS)
    except JWTError as e:
        six.raise_from(Unauthorized, e)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=env.get('PORT', 3000))