# 📱 Mobile Access Guide

## Access Your Stock Analysis App from Mobile Devices

Your application is now configured to be accessible from any device on your local WiFi network!

---

## 🌐 Access URLs

### From Your Computer (Mac):
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Keycloak:** http://localhost:8090

### From Mobile/Tablet/Other Devices on Same WiFi:
- **Frontend:** http://192.168.1.201:3000
- **Backend API:** http://192.168.1.201:8000
- **Keycloak:** http://192.168.1.201:8090

---

## 📋 Steps to Access from Mobile

### 1. Ensure Same WiFi Network
Make sure your mobile device is connected to the **same WiFi network** as your Mac (Krishnas-MacBook-Pro.local)

### 2. Open Browser on Mobile
Open any browser on your mobile device:
- Safari (iOS)
- Chrome (Android/iOS)
- Firefox
- Edge

### 3. Navigate to the App
Enter this URL in your mobile browser:
```
http://192.168.1.201:3000
```

### 4. Login
Use the same credentials:
- **Username:** admin
- **Password:** admin123

Or use the demo account:
- **Username:** demo
- **Password:** demo123

---

## 🔧 Troubleshooting

### Issue: Can't Access from Mobile

**Check 1: WiFi Connection**
- Ensure both Mac and mobile are on the same WiFi network
- Try pinging from mobile: Open terminal app and ping 192.168.1.201

**Check 2: Firewall Settings**
Your Mac's firewall might be blocking connections. To check:
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Ensure "Block all incoming connections" is NOT checked
4. Add Docker to allowed apps if needed

**Check 3: Docker is Running**
On your Mac, verify Docker containers are running:
```bash
docker-compose ps
```
All services should show "Up" status.

### Issue: "Connection Refused" Error

**Solution 1: Restart Services**
```bash
docker-compose restart frontend keycloak
```

**Solution 2: Check Mac IP Address**
Your IP might have changed (DHCP). Check current IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

If IP changed from 192.168.1.201, you need to update:
1. `docker-compose.yml` - Update VITE_API_URL and VITE_KEYCLOAK_URL
2. `keycloak/realm-export.json` - Update redirectUris and webOrigins
3. Rebuild: `docker-compose build frontend && docker-compose up -d`

### Issue: Authentication Fails on Mobile

**Solution:** Clear browser cache and cookies, then try again:
- Safari: Settings → Safari → Clear History and Website Data
- Chrome: Settings → Privacy → Clear Browsing Data

---

## 🎨 Mobile-Optimized UI

The application is already responsive and works great on mobile:
- ✅ Touch-friendly buttons
- ✅ Responsive card layout
- ✅ Mobile-optimized navigation
- ✅ Smooth animations

### Best Experience:
- **Portrait Mode:** Cards display in 1 column
- **Landscape Mode:** Cards display in 2 columns
- **Tablet:** Cards display in 3-4 columns

---

## 🔒 Security Notes

### Local Network Only
- This setup works only on your local WiFi network
- Not accessible from the internet (safe for testing)
- Perfect for personal use at home

### For Internet Access (Advanced)
If you want to access from anywhere:
1. **Option 1:** Use VPN (Tailscale, WireGuard)
2. **Option 2:** Set up port forwarding on router (less secure)
3. **Option 3:** Deploy to cloud (AWS, Azure, Heroku)

---

## 📊 Testing Connection

### From Mobile Terminal (Optional)
If you have a terminal app on mobile:

```bash
# Test connectivity
ping 192.168.1.201

# Test if port 3000 is open
nc -zv 192.168.1.201 3000

# Test if port 8090 is open (Keycloak)
nc -zv 192.168.1.201 8090
```

### Expected Results:
- All services should respond
- Ping time should be <10ms (same network)

---

## 🚀 Performance on Mobile

Expected performance on mobile devices:
- **Initial Load:** 3-5 seconds
- **API Calls:** <500ms
- **Page Navigation:** Instant
- **Stock Cards Load:** <1 second

---

## 📱 Mobile Browser Recommendations

### iOS (iPhone/iPad):
- **Safari** ✅ Best performance
- **Chrome** ✅ Good
- **Firefox** ✅ Good

### Android:
- **Chrome** ✅ Best performance
- **Firefox** ✅ Good
- **Samsung Internet** ✅ Good
- **Edge** ✅ Good

---

## 🔄 If IP Address Changes

Your Mac's IP address might change if you:
- Restart your router
- Reconnect to WiFi
- Use a different WiFi network

### Quick Fix Script:
Save this as `update-ip.sh`:

```bash
#!/bin/bash

# Get current IP
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')

echo "Current IP: $IP"
echo "Updating configuration..."

# Update docker-compose.yml
sed -i '' "s|VITE_API_URL: http://.*:8000|VITE_API_URL: http://$IP:8000|g" docker-compose.yml
sed -i '' "s|VITE_KEYCLOAK_URL: http://.*:8090|VITE_KEYCLOAK_URL: http://$IP:8090|g" docker-compose.yml

# Rebuild and restart
docker-compose build frontend
docker-compose up -d frontend
docker-compose restart keycloak

echo "Done! Access from mobile: http://$IP:3000"
```

Make it executable:
```bash
chmod +x update-ip.sh
```

Run it whenever IP changes:
```bash
./update-ip.sh
```

---

## 🎉 Quick Start Checklist

- [ ] Mac and mobile on same WiFi
- [ ] Docker containers running (`docker-compose ps`)
- [ ] Open http://192.168.1.201:3000 on mobile
- [ ] Login with admin/admin123
- [ ] Enjoy stock analysis on mobile!

---

## 💡 Tips for Best Mobile Experience

1. **Add to Home Screen:**
   - iOS: Safari → Share → Add to Home Screen
   - Android: Chrome → Menu → Add to Home Screen
   - Creates app-like icon on your home screen!

2. **Use Landscape Mode:**
   - Better view for stock cards
   - More cards visible at once

3. **Enable JavaScript:**
   - Required for the app to work
   - Should be enabled by default

4. **Disable Battery Saver:**
   - Can slow down animations
   - Better performance without it

---

## 📞 Need Help?

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Verify Docker containers are running
3. Ensure same WiFi network
4. Check Mac firewall settings
5. Try different mobile browser

---

**Current Configuration:**
- Mac IP: 192.168.1.201
- Mac Hostname: Krishnas-MacBook-Pro.local
- Frontend Port: 3000
- Backend Port: 8000
- Keycloak Port: 8090

**Last Updated:** November 22, 2025
