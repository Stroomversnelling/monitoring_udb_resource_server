import sqlalchemy
from sqlalchemy.ext.automap import automap_base
import random, string
from contextlib import contextmanager

roles = ['owner', 'inhabitant', 'gaurantee_provider', 'monitoring_service_provider', 'maintenance_provider','direct_service_provider']

def get_engine():
    return sql.create_engine('sqlite:///udb/sqlite/udb_resource_server.sqlite3')

def random_id_table(tblName = None):
    def random_id_for_table():
        tbl = Base.classes[tblName]
        newid = random_id()
        with session_scope() as session:
            while session.query(tbl).filter(tbl.__table__.name+'.'+tbl.__table__.name+'_id' == newid).limit(1).first() is not None:
                newid = random_id()
        return newid
    return random_id_for_table

def random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(20))


#these should be generated in the udb
new_user_id = random_id_table('user')
new_contract_id = random_id_table('contract')
#this should be generated on the pdb actually!
new_connection_id = random_id_table('contract')

#setup our database connection (sqlite for now)
sql = sqlalchemy
Base = automap_base()
engine = get_engine()

#start reflecting our database
Base.prepare(engine, reflect=True)
User = Base.classes.user
Connection = Base.classes.connection
Contract = Base.classes.contract
Pdb = Base.classes.pdb

#create a db session manager
Session = sql.orm.sessionmaker(bind=engine)


def empty_db():
    with session_scope() as session:
        print("Emptied contract table: "+str(session.query(Contract).delete()))
        print("Emptied connection table: "+str(session.query(Connection).delete()))
        print("Emptied pdb table: "+str(session.query(Pdb).delete()))
        print("Emptied user table: "+str(session.query(User).delete()))

@contextmanager
def session_scope():
    #Provide a transactional scope around a series of operations.
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()