import sys
import connexion
from connexion.resolver import RestyResolver
import time

import six
from werkzeug.exceptions import Unauthorized
from jose import JWTError, jwt

import sqlalchemy
from auth0.v3.management import Auth0

import random, string
import udb.config.udb_api_config as api_config
import udb.udb_db as udb


#https://auth0.com/docs/quickstart/backend/python/01-authorization
JWT_PUBLIC_KEY_SET = api_config.JWT_PUBLIC_KEY_SET
JWT_ALGORITHM = api_config.JWT_ALGORITHM
AUTH0_DOMAIN = api_config.AUTH0_DOMAIN
ISSUER = api_config.ISSUER
API_AUDIENCE = api_config.API_AUDIENCE

print(api_config.AUTH0_NAMESPACE)
PDB = api_config.AUTH0_NAMESPACE+"pdb_url"
print(PDB)

JWT_VERIFY_DEFAULTS = {
    'verify_signature': True, 
    'verify_aud': False, 
    'verify_iat': False, 
    'verify_exp': False, 
    'verify_nbf': False, 
    'verify_iss': True, 
    'verify_sub': False, 
    'verify_jti': False, 
    'verify_at_hash': False, 
    'leeway': 0,
}

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

def decode_token(token):
    print("Gonna print the token:", file=sys.stdout)
    print(jwt.get_unverified_header(token), file=sys.stdout)
    print(jwt.get_unverified_claims(token), file=sys.stdout)
    try:
        return jwt.decode(token, JWT_PUBLIC_KEY_SET, algorithms=[JWT_ALGORITHM], issuer=ISSUER, audience= API_AUDIENCE, options = JWT_VERIFY_DEFAULTS)
    except JWTError as e:
        six.raise_from(Unauthorized, e)

#currently no filtering or validation
def get_contract(user, token_info):
    response = []    
    pdb_url = None

    if PDB in token_info:
        pdb_url = token_info[PDB]
        print("Limiting for PDB: "+pdb_url, file=sys.stdout)

    with udb.session_scope() as session:
        result = None
        
        if pdb_url is None:
            result = session.execute("SELECT auth_user_id, connection_id, role, start, end, pdb_url FROM simple_contract WHERE auth_user_id = :auth_user_id", {'auth_user_id': user})
        else:
            result = session.execute("SELECT auth_user_id, connection_id, role, start, end, pdb_url FROM simple_contract WHERE auth_user_id = :auth_user_id AND pdb_url = :pdb_url", {'auth_user_id': user, 'pdb_url': pdb_url})

        if result is not None:
            for row in result:
                response.append({'connection_id': row.connection_id, 
                        'role': row.role,
                        'start': row.start,
                        'end': row.end,
                        'pdb_url': row.pdb_url
                    })
    
    return response

#currently no filtering or validation
def get_connection(user, token_info):
    response = []
    pdb_url = None

    if PDB in token_info:
        pdb_url = token_info[PDB]
        print("Limiting for PDB: "+pdb_url, file=sys.stdout)

    with udb.session_scope() as session:
        result = None
        
        if pdb_url is None:
            result = session.execute("SELECT connection_id, address, pdb_url FROM user_connection WHERE auth_user_id = :auth_user_id", {'auth_user_id': user})
        else:
            result = session.execute("SELECT connection_id, address, pdb_url FROM user_connection WHERE auth_user_id = :auth_user_id AND pdb_url = :pdb_url", {'auth_user_id': user, 'pdb_url': pdb_url})

        if result is not None:
            for row in result:
                response.append({'connection_id': row.connection_id,
                    'address': row.address,
                    'pdb_url': row.pdb_url
                })

    return response


#currently no filtering or validation
#should filter on user
def get_pdb(user, token_info):
    response = []
    pdb_url = None

    print("Checking "+PDB)
    if PDB in token_info:
        pdb_url = token_info[PDB]
        print("Limiting for PDB: "+pdb_url, file=sys.stdout)
    else:
        for i,o in enumerate(token_info):
            print(str(i)+" "+str(o)+" "+str(token_info[o]))

    with udb.session_scope() as session:
        result = None
        
        if pdb_url is None:
            result = session.execute("SELECT pdb_url FROM user_pdb WHERE auth_user_id = :auth_user_id", {'auth_user_id': user})
        else:
            result = session.execute("SELECT pdb_url FROM user_pdb WHERE auth_user_id = :auth_user_id AND pdb_url = :pdb_url", {'auth_user_id': user, 'pdb_url': pdb_url})

        if result is not None:
            for row in result:
                response.append(row.pdb_url)

    return response

if __name__ == '__main__':
    print("test")
    api = connexion.App(__name__, specification_dir='openapi3/')
    #app.add_api('energiesprong-user-0.0.2-swagger.yaml', resolver=RestyResolver('api'))
    api.add_api('energiesprong-user-0.0.2-swagger.yaml')
    api.run(port=8080)