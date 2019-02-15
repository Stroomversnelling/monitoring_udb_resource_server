import sqlalchemy
from auth0.v3.management import Auth0
from auth0.v3.exceptions import Auth0Error

import pandas as pd

import udb.config.udb_management_config as management_config
import time

from udb.udb_db import User, Connection, Pdb, Contract, new_user_id, new_contract_id, new_connection_id, session_scope, random, random_id, roles

from datetime import date, datetime, timedelta

#until we setup a queue / promises - dirty trick to avoid throttling errors with Auth0 - increase as necessary
time_to_wait = .200

#setup the Auth0 management SDK
auth0 = Auth0(domain = management_config.AUTH0_MANAGEMENT_DOMAIN, token = management_config.AUTH0_MANAGEMENT_TOKEN)

class UdbManagementException(Exception):
    pass

def get_auth0_connections():
    time.sleep(time_to_wait)
    return auth0.connections.all()

def get_auth0_users(page=0, per_page=100):
    time.sleep(time_to_wait)
    response = auth0.users.list(page=page, per_page=per_page, search_engine='v3')
    return response

def get_auth_user_by_email(email):
    if email is None: raise UdbManagementException("No email address given")
    time.sleep(time_to_wait)
    response = auth0.users_by_email.search_users_by_email(email)
    if len(response) != 1:
        raise UdbManagementException("Email is not an exact match")
    if not 'user_id' in response[0]:
        raise UdbManagementException("User id not found in Auth0 response.")
    return response[0]

def create_auth_user(email, password, name, body = None):
    if body is None:
        body = {"connection": "Username-Password-Authentication",
            "user_metadata": {"udb_test_user": True},
            "app_metadata": {"udb_test_user": True},
            "verify_email": False}
    body["email"] = email
    body["password"] = password
    body["name"] = name
    try:
        time.sleep(time_to_wait)
        response = auth0.users.create(body = body)
        return response
    except Auth0Error as e:
        print("Could not create user "+name+" with email "+email+": "+str(e))
        raise e

def create_udb_user(email = None, ignore_existing = None):
    if ignore_existing is None:
        ignore_existing = False

    existing_user = get_udb_user_by_email(email)
    if existing_user is not None:
        print(existing_user)
        if ignore_existing:
            print("There is already an existing user: "+email)
            return False
        else:
            raise UdbManagementException("Auth user ("+existing_user.user_id+"/"+existing_user.auth_user_id+") already added to the database: "+email)

    newuser = User(user_id=new_user_id(), 
        auth_user_id=get_auth_user_by_email(email)['user_id'], first_email=email)
    print("New user id: "+newuser.user_id)
    with session_scope() as session:
        session.add(newuser)
    return True

def create_udb_connection(connection_id = None, address = None, pdb_id = None):
    if connection_id is not None and address is not None and pdb_id is not None:
        newconnection = Connection(connection_id = connection_id,
            address = address, 
            pdb_id = pdb_id
            )
        with session_scope() as session:
            session.add(newconnection)
        return True
    else:
        return False

def get_udb_user_by_email(email):
    auth_user = get_auth_user_by_email(email)
    auth_user_id = auth_user['user_id']
    print("get_udb_user_by_email found user "+email+" with auth_user_id: "+auth_user_id)
    with session_scope() as session:
        response = session.query(User).filter(User.auth_user_id == auth_user_id).limit(1).first()
        if response is not None: session.expunge(response)
    return response

def get_udb_connection_by_id(connection_id):
    with session_scope() as session:
        response = session.query(Connection).filter(Connection.connection_id == connection_id).limit(1).first()
        if response is not None: session.expunge(response)
    return response

def get_udb_contract_by_id(contract_id):
    with session_scope() as session:
        response = session.query(Contract).filter(Contract.connection_id == contract_id).limit(1).first()
        if response is not None: session.expunge(response)
    return response

def get_pdb_id(pdb_url = None, auto_add = None):
    if auto_add is None: 
        auto_add = False
    #will need to add validation for url
    if pdb_url is None: raise UdbManagementException("Invalid PDB url: pdb_url passed is None")
    with session_scope() as session:
        pdb = session.query(Pdb).filter(Pdb.pdb_url == pdb_url).limit(1).first()
        if pdb is not None:
            return pdb.pdb_id
    if auto_add == True:
        create_pdb(pdb_url)
        return get_pdb_id(pdb_url)
    else:
        raise UdbManagementException("PDB url does not exist, add to database or add argument auto_add = True to get_pdb_id()")

def create_udb_contract(user, connection, role, start=None, end=None):
    #datetime.datetime.strptime("2008-09-03T20:56:35.450686Z", "%Y-%m-%dT%H:%M:%S.%fZ")
    if start is None:
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    if end is None:
        end = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    with session_scope() as session:
        session.add(Contract(contract_id = new_contract_id(), 
            user_id = user.user_id,
            connection_id = connection.connection_id,
            role = role,
            start = start,
            end = end
            ))
    return True

def create_pdb(pdb_url = None):
    if pdb_url is not None:
        with session_scope() as session:
            #for some reason the implicit auto increment does not automap so I manually create the PDB
            session.execute("INSERT INTO pdb (pdb_url) VALUES (:pdb_url)",
                    {'tbl': Pdb,'pdb_url_col': Pdb.pdb_url, 'pdb_url': pdb_url}
                )
        return get_pdb_id(pdb_url, auto_add = False)

def generate_random_test_data():
    #secret1234*()
    default_pass = "password1234*()"

    def generate_test_udb_connection(pdb_id):
        newid = new_connection_id()
        if create_udb_connection(newid, "Empty address", pdb_id):
            return newid

    def generate_auth_test_user(email_user, email_domain, password):
        body = {"connection": "Username-Password-Authentication",
            "user_metadata": {"udb_test_user": True},
            "app_metadata": {"udb_test_user": True},
            "email_verified": True,
            "verify_email": False,
            "nickname": "TESTUSER"}
        response = create_auth_user(email_user+"+"+random_id()+"@"+email_domain,
            password,
            "ND Test", 
            body = body)
        return response

    def generate_udb_test_user(password):
        response = generate_auth_test_user("some-user","fake-test-domain.com",password)
        if create_udb_user(email=response['email']):
            return get_udb_user_by_email(response['email'])
        else:
            return None

    newpdb_id = get_pdb_id("https://www.stroomversnelling/test-pdb/", auto_add = True)
    newusers = []
    newconnections = []

    for _ in range(5):
        newusers.append(generate_udb_test_user(default_pass))
    for _ in range(3):
        newconnection_id = generate_test_udb_connection(newpdb_id)
        newconnections.append(get_udb_connection_by_id(newconnection_id))
    for _ in range(15):
        try:
            create_udb_contract(user = random.choice(newusers),
            connection = random.choice(newconnections),
            role = random.choice(roles))
        except sqlalchemy.exc.IntegrityError as e:
            print("Collision "+str(e))
            pass
        finally:
            pass


def load_users_from_csv(csv_path, ignore_existing=None):
    #email, password, name
    if ignore_existing is None:
        ignore_existing = True
    with open(csv_path, 'r') as file:
        df = pd.read_csv(file)
        for _, r in df.iterrows():
            try:
                #the default body = None in create_auth_user will create a user with user metadata marking it as a test user for easy deletion.
                create_auth_user(r['email'], r['password'], r['name'])
            except Auth0Error as e:
                if ignore_existing == False:
                    raise e
            finally:
                try:
                    create_udb_user(r['email'], ignore_existing=ignore_existing)
                except UdbManagementException as e:
                    print("UDB Management exception while adding udb user "+r['email']+": "+str(e))


def load_connections_from_csv(csv_path, ignore_existing = None):
    #connection_id, address, pdb_url
    if ignore_existing is None:
        ignore_existing = True
    with open(csv_path, 'r') as file:
        df = pd.read_csv(file)
        for _, r in df.iterrows():
            existing = get_udb_connection_by_id(r['connection_id'])
            if existing is not None:
                if ignore_existing == False: 
                    raise UdbManagementException("Connection id "+r['connection_id']+" already in the database.")
            else:
                try:
                    pdb_id = get_pdb_id(pdb_url = r['pdb_url'], auto_add=True)
                    create_udb_connection(r['connection_id'], r['address'], pdb_id)
                except UdbManagementException as e:
                    print("UDB Management exception while adding connection: "+r['connection_id']+" / "+r['pdb_url']+":"+str(e))

def load_contracts_from_csv(csv_path, ignore_errors = None):
    #email, connection_id, role, start, end
    if ignore_errors is None:
        ignore_errors = True
    with open(csv_path, 'r') as file:
        df = pd.read_csv(file)
        for _, r in df.iterrows():
            try:
                create_udb_contract(user = get_udb_user_by_email(r['email']),
                    connection = get_udb_connection_by_id(r['connection_id']),
                    role = r['role'],
                    start = r['start'],
                    end = r['end'])
            except sqlalchemy.exc.IntegrityError as e:
                if ignore_errors == False:
                    raise e
                else:
                    print("Ignoring integrity error: "+str(e))

def delete_test_users():
    #to be defined
    users = get_auth0_users()
    for user in users['users']:
        print("Examining user "+user['email'])
        if ('user_metadata' in user and 'udb_test_user' in user['user_metadata'] and user['user_metadata']['udb_test_user'] == True) or ('app_metadata' in user and 'udb_test_user' in user['app_metadata'] and user['app_metadata']['udb_test_user'] == True):
            print("Deleting confirmed test user "+user['email'])
            time.sleep(time_to_wait)
            auth0.users.delete(id = user['user_id'])
        else:
            print(str(user))

