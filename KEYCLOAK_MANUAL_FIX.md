# 🔧 Manual Fix: Keycloak Redirect URI Configuration

## Quick Fix Instructions

Since the automatic script didn't work, follow these simple steps to manually update Keycloak:

### Step 1: Open Keycloak Admin Console

1. Open your browser and go to: **http://localhost:8090**
2. Click on **"Administration Console"**
3. Login with:
   - **Username:** admin
   - **Password:** admin123

### Step 2: Navigate to Client Settings

1. On the left sidebar, make sure you're in **"stock-analysis"** realm (top-left dropdown)
2. Click on **"Clients"** in the left menu
3. Find and click on **"stock-analysis-client"**

### Step 3: Update Redirect URIs

1. Scroll down to **"Valid redirect URIs"** section
2. You should see:
   ```
   http://localhost:3000/*
   http://localhost:8080/*
   ```

3. **ADD** these two new URIs (click "+ Add valid redirect URIs"):
   ```
   http://192.168.1.201:3000/*
   http://192.168.1.201:8080/*
   ```

4. The final list should be:
   ```
   http://localhost:3000/*
   http://localhost:8080/*
   http://192.168.1.201:3000/*
   http://192.168.1.201:8080/*
   ```

### Step 4: Update Web Origins

1. Scroll down to **"Web origins"** section
2. You should see:
   ```
   http://localhost:3000
   http://localhost:8080
   ```

3. **ADD** these two new origins:
   ```
   http://192.168.1.201:3000
   http://192.168.1.201:8080
   ```

4. **OR** simply add a wildcard (easier):
   ```
   *
   ```

### Step 5: Save

1. Scroll to the bottom
2. Click **"Save"** button
3. You should see a success message

---

## Alternative: Automated Script (Try Again)

If Keycloak takes time to start, try running this script after waiting:

```bash
cd /Users/krishnasonofgoddess/StockWithMetricsStrategy
./fix-keycloak.sh
```

---

## Verify It Works

After making the changes:

1. **From your mobile browser**, navigate to:
   ```
   http://192.168.1.201:3000
   ```

2. You should be redirected to Keycloak login page

3. Enter credentials:
   - Username: **admin**
   - Password: **admin123**

4. You should be logged in and see the Stock Analysis dashboard!

---

## Screenshots of What to Look For

### Keycloak Admin Console Login
```
┌─────────────────────────────────────┐
│  Keycloak                           │
│                                      │
│  Username: [admin            ]      │
│  Password: [••••••••         ]      │
│                                      │
│  [ Sign In ]                        │
└─────────────────────────────────────┘
```

### Client Settings Page
```
stock-analysis-client

Settings | Credentials | Roles | ... 

Client ID: stock-analysis-client
Name: Stock Analysis Client
Enabled: ON

Valid redirect URIs:
┌─────────────────────────────────────┐
│ http://localhost:3000/*             │ [×]
│ http://localhost:8080/*             │ [×]
│ http://192.168.1.201:3000/*         │ [×]
│ http://192.168.1.201:8080/*         │ [×]
└─────────────────────────────────────┘
[+ Add valid redirect URIs]

Web origins:
┌─────────────────────────────────────┐
│ http://localhost:3000               │ [×]
│ http://localhost:8080               │ [×]
│ http://192.168.1.201:3000           │ [×]
│ http://192.168.1.201:8080           │ [×]
└─────────────────────────────────────┘
[+ Add web origin]

[ Save ] [ Cancel ]
```

---

## Still Having Issues?

### Option 1: Delete and Recreate Keycloak

This will reset Keycloak completely:

```bash
cd /Users/krishnasonofgoddess/StockWithMetricsStrategy

# Stop and remove Keycloak
docker-compose stop keycloak postgres
docker-compose rm -f keycloak postgres

# Remove volumes (WARNING: This deletes all data!)
docker volume rm stockwithmetricsstrategy_postgres_data

# Start fresh
docker-compose up -d postgres keycloak

# Wait 30 seconds, then rebuild frontend
sleep 30
docker-compose build frontend
docker-compose up -d frontend
```

### Option 2: Add Wildcard (Easier)

In Keycloak admin console:
1. Go to **stock-analysis-client** settings
2. In **"Web origins"**, just add: `*`
3. This allows all origins (less secure but works for development)

---

## Current Configuration

- **Mac IP:** 192.168.1.201
- **Frontend URL:** http://192.168.1.201:3000
- **Backend URL:** http://192.168.1.201:8000
- **Keycloak URL:** http://192.168.1.201:8090

---

**Last Updated:** November 23, 2025
