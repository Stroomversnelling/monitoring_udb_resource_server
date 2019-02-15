from sqlalchemy.exc import IntegrityError
from auth0.v3.exceptions import Auth0Error

from udb.udb_management import UdbManagementException, session_scope, create_udb_user, get_auth0_users, random_id, random_id, load_connections_from_csv, load_users_from_csv, load_contracts_from_csv, create_pdb, generate_random_test_data, delete_test_users
from udb.udb_db import empty_db

def print_users():
    try:
        print(get_auth0_users())
    except Auth0Error as e:
        print(e)
        raise
    else:
        pass
    finally:
        pass

#use with caution!
def reset_all():
    def empty_test_users():
        print("Deleting test users from Auth0")
        delete_test_users()
    
    def empty_database():
        print("Emptying database")
        empty_db()
    
    empty_test_users()
    empty_database()

def create_fake_user():
    create_udb_user("faketestuser@stroomversnelling.nl", ignore_existing=True)

def create_fake_pdb():
    print(create_pdb("http://www.somerandom.pdb/"+random_id()))

def create_default_pdb():
    print(create_pdb("https://www.stroomversnelling/test-pdb/"))

#Example of generating random data
#generate_random_test_data()

"""try:
    create_default_pdb()
except IntegrityError as e:
    print("PDB could not be created: "+str(e))"""

#Safe one time loading
def load_test_data():
    reset_all()
    load_users_from_csv('./csv/testusers.csv', ignore_existing=False)
    load_connections_from_csv('./csv/testconnections.csv', ignore_existing=False)
    load_contracts_from_csv('./csv/testcontracts.csv', ignore_errors=False)

#Repeated loading and ignoring existing data with existing auth0 users
def reload_test_data():
    load_users_from_csv('./csv/testusers.csv', ignore_existing=True)
    load_connections_from_csv('./csv/testconnections.csv', ignore_existing=True)
    load_contracts_from_csv('./csv/testcontracts.csv', ignore_errors=True)

#reset test data
#load_test_data()

#Example of retrieving the contracts in simple format to display after the script is run

with session_scope() as session:
    result = session.execute("SELECT simple_contract.connection_id AS connection_id, connection.address AS address, pdb_url FROM simple_contract LEFT JOIN connection ON simple_contract.connection_id = connection.connection_id GROUP BY simple_contract.connection_id")
    for row in result:
        print(row.connection_id+" "+row.pdb_url)

    result = session.execute("SELECT simple_contract.connection_id AS connection_id, connection.address AS address, pdb_url FROM simple_contract LEFT JOIN connection ON simple_contract.connection_id = connection.connection_id WHERE auth_user_id = :auth_user_id GROUP BY simple_contract.connection_id", {'auth_user_id': "auth0|5c643c5fcfaebb3d1dc27e65"})
    for row in result:
        print(row.pdb_url)

    result = session.execute("SELECT * FROM user_connection WHERE auth_user_id = :auth_user_id", {'auth_user_id': "auth0|5c643c61cfaebb3d1dc27e66"})
    for row in result:
        print(row.connection_id+" "+row.pdb_url+" "+row.auth_user_id)

    print(" --- ")

    result = session.execute("SELECT * FROM user_pdb WHERE auth_user_id = :auth_user_id", {'auth_user_id': "auth0|5c643c5fcfaebb3d1dc27e65"})
    for row in result:
        print(row.pdb_url+" "+row.auth_user_id)