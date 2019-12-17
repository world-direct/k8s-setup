# NOTE: This is far away from being a complete OIDC Test-Script!
# - it contains assumptions about the kind of responses (e.g. redirection to /approval)
# - it contains assumptions about urls being relative or absolute
# - it parses the HTML form with regex, not with a HTML parser

# input data (values have to match the 'dex' configmap, see templates/configmap.yaml)
prov=https://dex.k8stest.local/.well-known/openid-configuration
client_id=kubernetes
client_secret=5a0a502aa7fa1fa829e02bdca5f21c11
redirect_uri=http://localhost:5555/callback
login=admin@example.com
password=password

# get endpoints
oidconf=$(curl $prov -k)
issuer=$(echo $oidconf | jq ".issuer" -r)
authep=$(echo $oidconf | jq ".authorization_endpoint" -r)
tokenep=$(echo $oidconf | jq ".token_endpoint" -r)

echo "*** Issuer: $issuer"
echo "*** Authorization-Endpoint: $authep"
echo "*** Token-Endpoint: $tokenep"

# request token (open form)
redirect_uri=http://127.0.0.1:5555/callback
function uriencode { jq -nr --arg v "$1" '$v|@uri'; }
authreq="$authep?response_type=code&scope=openid&client_id=$client_id&redirect_uri=$(uriencode $redirect_uri)"
authres=$(curl -kL $authreq)

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
approval_rel=$(curl -ki \
    --data-urlencode "login=$login" \
    --data-urlencode "password=$password"  \
    $form_action \
    | grep "location: " \
    | awk '{print $2}' \
    | tr -d '\n\r')

approval=$issuer$approval_rel
echo "*** Approval-Url: $approval" #  no OIDC standard, dex impl. detail

# get the auth_code by fetching approval, but without executing 302 to redirect_url
location=$(curl -ki $approval \
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

# get token
curl -kv \
    --data-urlencode "grant_type=authorization_code" \
    --data-urlencode "code=$authcode" \
    --data-urlencode "redirect_uri=$redirect_uri"   \
    --data-urlencode "client_id=$client_id"   \
    --data-urlencode "client_secret=$client_secret"   \
    "$tokenep" | jq