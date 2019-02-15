# UDB Resource Server and Client
This repository provides tools to test a User Database Resources Server for Energy Performance Monitoring.

## Installation
1. Create an Auth0 account (free) to be create an dashboard where you can add the UDB API, the management app, and the client app. 

For the api choose an identifier such as "https://stroomversnelling.nl/user/test" and give it a name. Set the signing algorithm to RS256.

The apps require secret keys and some minimal configuration. You should create a web app for the client or native app (both will support authorization code flow). You should create a M2M app for the management app with access to the Auth0 management API. 

For the client:
Add redirect URIs / callback path to the default https://localhost:3000/ or adapt as required.
Add custom logout paths: https://localhost:3000/

In the Auth0 dashboard (https://manage.auth0.com/): Add a custom rules and hooks to enable the creation of the PDB tokens dynamically with custom claims in the JWT format bearer token.

Add the following rule for the client to work:
~~~~
function (user, context, callback) {
  const namespace = 'https://stroomversnelling.nl/';
  
  context.accessToken[namespace+"test"] = "passed";
  
  console.log("Running rule");
  if (typeof context.request.query !== 'undefined') {
    console.log("There is a query of length"+context.request.query.length);
    for (var i in context.request.query) {
      console.log(i);
    }
    if (typeof context.request.query.pdb_url !== 'undefined') {
      console.log("There is a PDB url and will try to generate a custom claim.");      
	    context.accessToken[namespace + 'pdb_url'] = context.request.query.pdb_url;
    }
  }
  callback(null, user, context);
}
~~~~
The management app will work with the Auth0 Management API. However, if you want the M2M flow to work for the UDB API (you have to implement this or use curl), then you will need to add a hook that does the same as the rule (this is untested):
~~~~
/**
@param {object} client - information about the client
@param {string} client.name - name of client
@param {string} client.id - client id
@param {string} client.tenant - Auth0 tenant name
@param {object} client.metadata - client metadata
@param {array|undefined} scope - array of strings representing the scope claim or undefined
@param {string} audience - token's audience claim
@param {object} context - additional authorization context
@param {object} context.webtask - webtask context
@param {function} cb - function (error, accessTokenClaims)
*/
module.exports = function(client, scope, audience, context, cb) {
  console.log("Inside hook");
  var access_token = {};
  access_token.scope = scope;
  const namespace = 'https://stroomversnelling.nl/';
    
  if (typeof context.request.query !== 'undefined') {
    console.log("There is a query of length"+context.request.query.length);
    for (var i in context.request.query) {
      console.log(i);
    }
    if (typeof context.request.query.pdb_url !== 'undefined') {
      console.log("There is a PDB url and will try to generate a custom claim.");      
	    access_token[namespace + 'pdb_url'] = context.request.query.pdb_url;
    }
  }

  console.log("Scope is "+scope);
  console.log("pdb_url is "+access_token["pdb_url"]);

  // Modify scopes or add extra claims
  // access_token['https://example.com/claim'] = 'bar';
  // access_token.scope.push('extra');

  cb(null, access_token);
};
~~~~
2. Review and modify the config files in the config folder. Remove the ".example" extension

To get your public key go to:
https://[your-domain].auth0.com/.well-known/jwks.json

3. Review and remove the ".example" extension from the sqlite database

4. Create csv files such as in the csv folder with the appropriate users, connection IDs (random 20 char alphanumeric), and contracts. Review the example sqlite database if in doubt about how the data is structured and constrained. Some constraints, for example on data format are only enforced through the python management app on import.

5. Generate a permanent token for your management app

python management_token.py

Paste the result into the variable AUTH0_MANAGEMENT_TOKEN in config/udp_management_config.py

# How to use it
## Start up the API 
This will default to http://localhost:8080/energiesprong/user/0.0.3/ui/

python app.py

## Run the management script
This one will let up load csv files, create users, etc. Look at the code for options.

python management_app.py

## Run the client app for login and to get PDB tokens
This client allows you to either login and create a token for the UDB to see all PDBs (what a client would do for the user) and related data. The PDB field on the home page however allows you to specify the token is for one specific PDB and will limit results to only PDBs that have the exact URL filled in. So if you PDB url in the database is "https://www.stroomversnelling/pdb-example" then you must use this value exactly to generate a valid token. The token works by adding a custom scope using the rule above, which will limit the data provided via the API.

python authorization_client.py