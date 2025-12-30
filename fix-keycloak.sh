#!/bin/bash

echo "🔧 Fixing Keycloak Redirect URIs..."
echo "Waiting for Keycloak to be ready..."
sleep 20

# Get admin token
echo "Getting admin token..."
TOKEN=$(curl -s -X POST "http://localhost:8090/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin123" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get admin token. Is Keycloak running?"
    exit 1
fi

echo "✅ Got admin token"

# Get client ID
echo "Fetching client configuration..."
CLIENT_UUID=$(curl -s -X GET "http://localhost:8090/admin/realms/stock-analysis/clients" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -c "import sys, json; clients = json.load(sys.stdin); print([c['id'] for c in clients if c['clientId'] == 'stock-analysis-client'][0])" 2>/dev/null)

if [ -z "$CLIENT_UUID" ]; then
    echo "❌ Failed to get client UUID"
    exit 1
fi

echo "✅ Found client UUID: $CLIENT_UUID"

# Update client with new redirect URIs
echo "Updating redirect URIs..."
curl -s -X PUT "http://localhost:8090/admin/realms/stock-analysis/clients/$CLIENT_UUID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "stock-analysis-client",
    "name": "Stock Analysis Client",
    "enabled": true,
    "publicClient": true,
    "directAccessGrantsEnabled": true,
    "standardFlowEnabled": true,
    "redirectUris": [
      "http://localhost:3000/*",
      "http://localhost:8080/*",
      "http://192.168.1.201:3000/*",
      "http://192.168.1.201:8080/*"
    ],
    "webOrigins": [
      "http://localhost:3000",
      "http://localhost:8080",
      "http://192.168.1.201:3000",
      "http://192.168.1.201:8080",
      "*"
    ],
    "attributes": {
      "post.logout.redirect.uris": "+",
      "backchannel.logout.session.required": "true",
      "backchannel.logout.revoke.offline.tokens": "false"
    }
  }'

echo ""
echo "✅ Keycloak redirect URIs updated!"
echo ""
echo "📱 You can now access from mobile:"
echo "   http://192.168.1.201:3000"
echo ""
echo "🔐 Login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
