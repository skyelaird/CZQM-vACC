# CZQM MAESTRO Server - Deployment Guide

## Overview

This server enables multi-user synchronization of MAESTRO arrival sequence data between controllers. It implements a Master/Slave architecture where:

- **MASTER**: One controller per airport manages the sequence (typically APP or dedicated Planner)
- **SLAVE**: Other controllers (ACC, TWR) receive read-only sequence data

## Prerequisites

- Node.js 16+ installed
- Access to a server (VPS, cloud instance, or local machine)
- Port 3000 available (or configure different port)

## Installation

### Local Development

```bash
# Install dependencies
npm install

# Start server
npm start

# Or for development with auto-reload
npm run dev
```

### Production Deployment (Linux VPS)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Create application directory
sudo mkdir -p /opt/czqm-maestro
cd /opt/czqm-maestro

# 4. Copy files
# Upload czqm-maestro-server.js and package.json to this directory

# 5. Install dependencies
npm install --production

# 6. Create systemd service
sudo nano /etc/systemd/system/czqm-maestro.service
```

**Service file content:**
```ini
[Unit]
Description=CZQM MAESTRO Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/czqm-maestro
ExecStart=/usr/bin/node czqm-maestro-server.js
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable czqm-maestro
sudo systemctl start czqm-maestro

# 8. Check status
sudo systemctl status czqm-maestro

# 9. View logs
sudo journalctl -u czqm-maestro -f
```

### Using PM2 (Alternative)

```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start czqm-maestro-server.js --name czqm-maestro

# Configure auto-start on reboot
pm2 startup
pm2 save

# View logs
pm2 logs czqm-maestro
```

## Configuration

### Adding More Airports

Edit `czqm-maestro-server.js` and add to the `sequenceData` object:

```javascript
const sequenceData = {
  CYQX: { master: null, sequence: [], lastUpdate: null },
  CYHZ: { master: null, sequence: [], lastUpdate: null },
  CYYT: { master: null, sequence: [], lastUpdate: null },
  CYYR: { master: null, sequence: [], lastUpdate: null }, // Add new airports
};
```

### Changing Port

Modify the `port` variable at the top of the file:

```javascript
const port = 8080; // Change from 3000 to 8080
```

### Configuring MAESTRO Plugin

In your MAESTRO plugin configuration, you'll need to set the server URL. This depends on the plugin's configuration format, but typically:

**TopSkyAirports.txt or similar:**
```
CYQX_AMAN_SERVER=http://your-server-ip:3000
CYHZ_AMAN_SERVER=http://your-server-ip:3000
CYYT_AMAN_SERVER=http://your-server-ip:3000
```

## Nginx Reverse Proxy (Recommended for Production)

If you want to use SSL/HTTPS:

```bash
sudo apt install nginx

sudo nano /etc/nginx/sites-available/czqm-maestro
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name maestro.czqm.ca;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/czqm-maestro /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Install SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d maestro.czqm.ca
```

## API Endpoints

### Health Check
```
GET /health
```

### System Status
```
GET /api/maestro/status
```

### Register as MASTER
```
POST /api/maestro/CYQX/master
Body: { "controllerId": "CZQX_APP", "frequency": "127.700" }
```

### Update Sequence (MASTER only)
```
PUT /api/maestro/CYQX/sequence
Body: { 
  "controllerId": "CZQX_APP", 
  "sequence": [
    {
      "callsign": "ACA123",
      "sequence": 1,
      "sta": "2025-11-30T18:45:00Z",
      "runway": "29",
      "delay": 3
    }
  ]
}
```

### Get Sequence (SLAVE)
```
GET /api/maestro/CYQX/sequence
```

### Heartbeat
```
POST /api/maestro/CYQX/heartbeat
Body: { "controllerId": "CZQX_APP" }
```

### Release MASTER
```
DELETE /api/maestro/CYQX/master
Body: { "controllerId": "CZQX_APP" }
```

## Monitoring

### Check if server is running
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{"status":"ok","timestamp":"2025-11-30T18:00:00.000Z"}
```

### Check current status
```bash
curl http://localhost:3000/api/maestro/status
```

## Firewall Configuration

```bash
# Allow port 3000 (or your configured port)
sudo ufw allow 3000/tcp

# Or if using Nginx reverse proxy
sudo ufw allow 'Nginx Full'
```

## Security Considerations

1. **Authentication**: Current version has no authentication. For production, consider:
   - VATSIM SSO integration
   - API keys per controller
   - IP whitelist

2. **Rate Limiting**: Add rate limiting to prevent abuse:
   ```bash
   npm install express-rate-limit
   ```

3. **HTTPS**: Always use HTTPS in production (via Nginx + Let's Encrypt)

4. **Logging**: Current logs go to console. Consider:
   - Winston for structured logging
   - Log rotation with logrotate
   - Centralized logging (Papertrail, Loggly, etc.)

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
sudo lsof -i :3000

# Check logs
sudo journalctl -u czqm-maestro -n 50
```

### Can't connect from EuroScope
- Verify server is running: `curl http://localhost:3000/health`
- Check firewall rules
- Verify MAESTRO plugin configuration has correct server URL
- Check CORS headers are being sent

### MASTER gets stuck/won't release
- MASTER connections auto-timeout after 2 minutes without heartbeat
- Manual reset: Restart the server

## Backup and Recovery

### Data Persistence

Current version stores data in memory. For persistence across restarts:

1. **Option 1: Redis**
   ```bash
   npm install redis
   ```
   Replace in-memory storage with Redis

2. **Option 2: SQLite**
   ```bash
   npm install better-sqlite3
   ```
   Store sequences in SQLite database

3. **Option 3: PostgreSQL/MySQL**
   For enterprise deployment

## Support

For issues or questions:
- CZQM Operations: ops@czqm.ca (replace with actual contact)
- GitHub Issues: [your repository]
- VATCAN Discord: #czqm-tech-support

## License

GPL-3.0 - See LICENSE file for details
