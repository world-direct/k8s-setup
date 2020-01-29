# NOTE: This is far away from being a complete OIDC Test-script!
# - it contains assumptions about the kind of responses (e.g. redirection to /approval)
# - it contains assumptions about urls being relative or absolute
# - it parses the HTML form with regex, not with a HTML parser

# input data (values have to match the 'dex' configmap, see templates/configmap.yaml)
prov=https://auth.k8stest.local/.well-known/openid-configuration
client_id=kubernetes
client_secret=5a0a502aa7fa1fa829e02bdca5f21c11
redirect_uri=http://localhost:5555/callback
login=admin@example.com
password=password

# get endpoints
oidconf=$(curl -s $prov -k)
issuer=$(echo $oidconf | jq ".issuer" -r)
authep=$(echo $oidconf | jq ".authorization_endpoint" -r)
tokenep=$(echo $oidconf | jq ".token_endpoint" -r)

echo "*** Issuer: $issuer"
echo "*** Authorization-Endpoint: $authep"
echo "*** Token-Endpoint: $tokenep"

# request token (open form)
redirect_uri=http://127.0.0.1:5555/callback
function uriencode { jq -nr --arg v "$1" '$v|@uri'; }
authreq="$authep?response_type=code&scope=openid%20offline_access&client_id=$client_id&redirect_uri=$(uriencode $redirect_uri)"
authres=$(curl -s -kL $authreq)

# extract the 'action' from the form
form_action=
if [[ "$authres" =~ 'action='\"([^\"]+)\" ]]; then 
    form_action_rel=${BASH_REMATCH[1]};

    # form_action is a relative url, so add the issuer
    form_action=$issuer$form_action_rel
    echo "*** Form-Action: $form_action"
fi

# submitting the login-form
# we expect a redirection to /approval?req=r5otb2asnqq4heo3e4rbnqfzm
# we can't use just -L, because we need to catch the redirect to redirect_uri
approval_rel=$(curl -s -ki \
    --data-urlencode "login=$login" \
    --data-urlencode "password=$password"  \
    $form_action \
    | grep "location: " \
    | awk '{print $2}' \
    | tr -d '\n\r')

approval=$issuer$approval_rel
echo "*** Approval-Url: $approval" #  no OIDC standard, dex impl. detail

# get the auth_code by fetching approval, but without executing 302 to redirect_url
location=$(curl -s -ki $approval \
    | grep "location: " \
    | awk '{print $2}' \
    | tr -d '\n\r')


authcode=
if [[ "$location" =~ 'code='([a-z0-9]+) ]]; then 
    authcode=${BASH_REMATCH[1]}; 
else
    echo "unexpected response"
fi

echo "*** Authcode: $authcode"

# get id_token and refresh_token
full_token=$(
curl -s -k \
    --data-urlencode "grant_type=authorization_code" \
    --data-urlencode "code=$authcode" \
    --data-urlencode "redirect_uri=$redirect_uri"   \
    --data-urlencode "client_id=$client_id"   \
    --data-urlencode "client_secret=$client_secret"   \
    "$tokenep" )

# echo $full_token | jq
refresh_token=$(echo $full_token | jq ".refresh_token" -r)
echo "*** Refresh-Token: $refresh_token"

# get id_token from refresh_token
refreshed_token=$(
    curl -s -k \
    --data-urlencode "grant_type=refresh_token" \
    --data-urlencode "refresh_token=$refresh_token" \
    --data-urlencode "client_id=$client_id"   \
    --data-urlencode "client_secret=$client_secret"   \
    "$tokenep")
    
# echo $refreshed_token| jq
id_token=$(echo $refreshed_token | jq ".id_token" -r)
echo "*** id-Token: $id_token"

echo "*** Test Commands"

# print kubectl register command
# https://kubernetes.io/docs/reference/access-authn-authz/authentication/#option-1-oidc-authenticator

kubectl config set-credentials OIDC \
  --auth-provider oidc \
  --auth-provider-arg=idp-issuer-url=$issuer \
  --auth-provider-arg=client-id=$client_id \
  --auth-provider-arg=client-secret=$client_secret \
  --auth-provider-arg=refresh-token=$refresh_token \
  --auth-provider-arg=idp-certificate-authority=$HOME/.k8s-setup/cacrt.pem \
  --auth-provider-arg=id-token=$id_token

# https://kubernetes.io/docs/reference/access-authn-authz/authentication/#option-2-use-the-token-option
# echo kubectl --token=$id_token get nodes

kubectl config set-context OIDC@k8stest.local \
    --cluster=k8stest.local \
    --namespace=default \
    --user=OIDC

