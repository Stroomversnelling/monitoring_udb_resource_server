from auth0.v3.authentication import GetToken
import udb.config.udb_management_config as config

#This is for generating a test management token - not necessarily the right way to do this.

domain = config.AUTH0_MANAGEMENT_DOMAIN
non_interactive_client_id = config.AUTH0_MANAGEMENT_CLIENT_ID
non_interactive_client_secret = config.AUTH0_MANAGEMENT_CLIENT_SECRET

get_token = GetToken(domain)
token = get_token.client_credentials(non_interactive_client_id,
    non_interactive_client_secret, 'https://{}/api/v2/'.format(domain))
mgmt_api_token = token['access_token']

print(token['access_token'])