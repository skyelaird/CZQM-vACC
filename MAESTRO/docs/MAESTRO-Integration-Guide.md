# MAESTRO Plugin Integration Guide
## Connecting MAESTRO to CZQM Server

---

## Overview

This guide explains how to modify the MAESTRO plugin to communicate with your CZQM server for multi-user synchronization.

**Note:** MAESTRO was designed by Juha Holopainen with local file-based sharing. We're extending it to use a centralized server.

---

## Architecture

```
┌─────────────────┐
│  EuroScope +    │
│  MAESTRO Plugin │◄──┐
└─────────────────┘   │
                      │ HTTP/HTTPS
┌─────────────────┐   │
│  EuroScope +    │◄──┼──► ┌──────────────────┐
│  MAESTRO Plugin │   │     │  CZQM MAESTRO    │
└─────────────────┘   │     │     Server       │
                      │     │  (Node.js API)   │
┌─────────────────┐   │     └──────────────────┘
│  EuroScope +    │◄──┘
│  MAESTRO Plugin │
└─────────────────┘

   Controller 1        Multiple          Centralized
   Controller 2      Controllers           Server
   Controller 3
```

---

## Option 1: Configuration File Approach (Easiest)

If MAESTRO supports external configuration, add a config file:

### Create CZQM_MAESTRO_Config.txt

```ini
[Server]
Enabled=1
URL=http://maestro.czqm.ca:3000
Timeout=5000
HeartbeatInterval=30000

[Airports]
CYHZ=1
CYYT=1
CYQX=1
CYYR=0

[Connection]
AutoReconnect=1
RetryAttempts=3
RetryDelay=5000

[Features]
LocalFallback=1
CacheTimeout=60000
```

Place in: `Documents\EuroScope\MAESTRO\`

---

## Option 2: Plugin Wrapper (Recommended)

Create a wrapper DLL that intercepts MAESTRO's file operations and redirects to server.

### CZQM_MAESTRO_Connector.dll

This wrapper sits between EuroScope and MAESTRO:

**Functionality:**
1. Intercepts MAESTRO's local file read/write
2. Converts to HTTP API calls
3. Handles Master/Slave logic
4. Falls back to local files if server unavailable

**Implementation needed:** (C++ development)

```cpp
// Pseudo-code structure
class CZQMConnector {
public:
    // Intercept MAESTRO file writes
    bool WriteSequence(AirportCode airport, SequenceData data) {
        if (serverAvailable) {
            return SendToServer(airport, data);
        } else {
            return WriteToLocalFile(airport, data);
        }
    }
    
    // Intercept MAESTRO file reads
    SequenceData ReadSequence(AirportCode airport) {
        if (serverAvailable) {
            return FetchFromServer(airport);
        } else {
            return ReadFromLocalFile(airport);
        }
    }
    
    bool SendToServer(AirportCode airport, SequenceData data) {
        HttpClient client;
        return client.PUT(
            serverUrl + "/api/maestro/" + airport + "/sequence",
            { "controllerId": controllerId, "sequence": data }
        );
    }
};
```

---

## Option 3: Modified MAESTRO Plugin (Advanced)

If you have access to MAESTRO source code, modify it directly.

### Required Changes

**1. Add HTTP client library**
```cpp
#include <curl/curl.h>  // libcurl for HTTP requests
```

**2. Add server configuration**
```cpp
class ServerConfig {
    std::string serverUrl;
    std::string controllerId;
    bool useServer;
    int timeout;
};
```

**3. Modify sequence save function**
```cpp
// Original MAESTRO (file-based)
void SaveSequence(Airport airport, Sequence seq) {
    std::ofstream file("sequence_" + airport + ".json");
    file << SerializeSequence(seq);
    file.close();
}

// Modified for CZQM (server-based)
void SaveSequence(Airport airport, Sequence seq) {
    if (config.useServer && IsMaster(airport)) {
        SendSequenceToServer(airport, seq);
    }
    
    // Still save locally as backup
    std::ofstream file("sequence_" + airport + ".json");
    file << SerializeSequence(seq);
    file.close();
}

void SendSequenceToServer(Airport airport, Sequence seq) {
    CURL* curl = curl_easy_init();
    std::string url = config.serverUrl + "/api/maestro/" + 
                      airport + "/sequence";
    
    json body = {
        {"controllerId", config.controllerId},
        {"sequence", SerializeSequence(seq)}
    };
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.dump().c_str());
    
    CURLcode res = curl_easy_perform(curl);
    
    if (res != CURLE_OK) {
        Log("Failed to send sequence to server: " + 
            std::string(curl_easy_strerror(res)));
    }
    
    curl_easy_cleanup(curl);
}
```

**4. Modify sequence load function**
```cpp
// Modified for CZQM (server-based)
Sequence LoadSequence(Airport airport) {
    Sequence seq;
    
    if (config.useServer) {
        seq = FetchSequenceFromServer(airport);
        if (!seq.empty()) {
            return seq;
        }
    }
    
    // Fallback to local file
    std::ifstream file("sequence_" + airport + ".json");
    if (file.good()) {
        seq = DeserializeSequence(file);
    }
    
    return seq;
}
```

**5. Add Master registration**
```cpp
bool RegisterAsMaster(Airport airport) {
    CURL* curl = curl_easy_init();
    std::string url = config.serverUrl + "/api/maestro/" + 
                      airport + "/master";
    
    json body = {
        {"controllerId", GetCallsign()},
        {"frequency", GetFrequency()}
    };
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.dump().c_str());
    
    CURLcode res = curl_easy_perform(curl);
    bool success = (res == CURLE_OK);
    
    curl_easy_cleanup(curl);
    return success;
}
```

**6. Add heartbeat timer**
```cpp
void StartHeartbeat() {
    heartbeatTimer = SetTimer(NULL, 0, 30000, HeartbeatCallback);
}

void CALLBACK HeartbeatCallback(HWND hwnd, UINT msg, 
                                 UINT_PTR id, DWORD time) {
    if (isMaster) {
        SendHeartbeat();
    }
}

void SendHeartbeat() {
    CURL* curl = curl_easy_init();
    std::string url = config.serverUrl + "/api/maestro/" + 
                      currentAirport + "/heartbeat";
    
    json body = {{"controllerId", GetCallsign()}};
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.dump().c_str());
    curl_easy_perform(curl);
    curl_easy_cleanup(curl);
}
```

---

## Option 4: External Synchronization Tool

Create a separate tool that runs alongside EuroScope:

### CZQM_MAESTRO_Sync.exe

**How it works:**
1. Monitors MAESTRO's local files for changes
2. When Master writes file, uploads to server
3. When Slave, downloads from server and writes locally
4. MAESTRO reads local files as normal (unaware of sync)

**Advantages:**
- No MAESTRO modification needed
- Easy to develop (Python/C#)
- Can be updated independently

**Disadvantages:**
- File watching has small delay
- Slightly less efficient than direct integration

### Python Implementation Example

```python
import time
import json
import requests
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MAESTROSyncHandler(FileSystemEventHandler):
    def __init__(self, server_url, controller_id, is_master):
        self.server_url = server_url
        self.controller_id = controller_id
        self.is_master = is_master
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if "sequence_" in event.src_path and self.is_master:
            # Master wrote sequence - upload to server
            airport = extract_airport_from_filename(event.src_path)
            with open(event.src_path, 'r') as f:
                sequence = json.load(f)
            
            self.upload_sequence(airport, sequence)
    
    def upload_sequence(self, airport, sequence):
        url = f"{self.server_url}/api/maestro/{airport}/sequence"
        data = {
            "controllerId": self.controller_id,
            "sequence": sequence
        }
        requests.put(url, json=data)
        
    def sync_from_server(self):
        # Slave periodically fetches from server
        airports = ['CYHZ', 'CYYT', 'CYQX']
        
        for airport in airports:
            url = f"{self.server_url}/api/maestro/{airport}/sequence"
            response = requests.get(url)
            
            if response.ok:
                data = response.json()
                filepath = f"sequence_{airport}.json"
                
                with open(filepath, 'w') as f:
                    json.dump(data['sequence'], f)

# Main loop
observer = Observer()
handler = MAESTROSyncHandler(
    server_url="http://maestro.czqm.ca:3000",
    controller_id="YHZ_APP",
    is_master=True
)

observer.schedule(handler, path="Documents/EuroScope/MAESTRO", recursive=False)
observer.start()

try:
    while True:
        if not handler.is_master:
            handler.sync_from_server()
        time.sleep(5)
except KeyboardInterrupt:
    observer.stop()

observer.join()
```

---

## Recommended Implementation Path

### Phase 1: External Sync Tool (Quick Win)
1. **Week 1**: Develop Python sync tool
2. **Week 2**: Test with 2-3 controllers
3. **Week 3**: Deploy for all controllers
4. **Effort**: Low, ~20 hours development

### Phase 2: Configuration Integration (Better UX)
1. **Month 2**: Add config file support to MAESTRO (if possible)
2. **Month 2**: Update documentation
3. **Effort**: Medium, depends on MAESTRO source access

### Phase 3: Native Integration (Best Experience)
1. **Month 3-4**: Modify MAESTRO plugin directly
2. **Month 4**: Extensive testing
3. **Month 5**: Production deployment
4. **Effort**: High, 40-80 hours if source available

---

## Testing Procedure

### Local Testing
```bash
# Terminal 1: Start server
cd /opt/czqm-maestro
npm start

# Terminal 2: Test endpoints
curl http://localhost:3000/health
curl http://localhost:3000/api/maestro/status
```

### Multi-User Testing

**Setup:**
1. Two EuroScope instances on separate computers
2. Load MAESTRO on both
3. Connect one as MASTER, one as SLAVE

**Test Cases:**
1. ✅ MASTER can connect
2. ✅ SLAVE sees MASTER's data
3. ✅ MASTER updates sequence, SLAVE receives update
4. ✅ MASTER disconnects, SLAVE sees change
5. ✅ New MASTER can take over
6. ✅ Server restarts, data persists (if using database)

---

## Troubleshooting Integration

### Plugin won't connect to server

**Check:**
1. Server is running: `curl http://your-server:3000/health`
2. Firewall allows connections
3. URL is correct in configuration
4. Plugin has network permissions

### Sequence not updating

**Check:**
1. MASTER is actually sending data (check server logs)
2. SLAVE is polling server regularly
3. Airport code matches exactly
4. No network errors in plugin log

### Performance issues

**Solutions:**
1. Reduce polling frequency for SLAVE
2. Implement caching in sync tool
3. Use websockets instead of HTTP polling
4. Optimize JSON serialization

---

## Support and Resources

**MAESTRO Plugin:**
- Original Author: Juha Holopainen
- Forum: https://forum.vatsim-scandinavia.org/

**CZQM Development:**
- GitHub: [your repository]
- Discord: #czqm-dev
- Email: dev@czqm.ca

---

**Next Steps:**
1. Choose implementation approach
2. Set up development environment
3. Deploy server (see DEPLOYMENT.md)
4. Implement sync mechanism
5. Test with controllers
6. Deploy to production
7. Train controllers (see Training Guide)

Good luck with the integration!
