#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import threading
import time
from datetime import datetime

PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

def load_clans():
    if os.path.exists("clans.json"):
        with open("clans.json", "r") as f:
            return json.load(f)
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def save_clans(clans):
    with open("clans.json", "w") as f:
        json.dump(clans, f, indent=2)

def load_donations():
    if os.path.exists("donations.json"):
        with open("donations.json", "r") as f:
            return json.load(f)
    return {}

def save_donations(data):
    with open("donations.json", "w") as f:
        json.dump(data, f, indent=2)

def get_clan_data(clan_tag):
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe="")
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_KEY}")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_donations():
    donations = load_donations()
    clans = load_clans()
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        
        if clan_key not in donations:
            donations[clan_key] = {
                "clan_info": {},
                "players": {}
            }
        
        donations[clan_key]["clan_info"] = {
            "name": clan_data.get("name", ""),
            "members": clan_data.get("members", 0),
            "points": clan_data.get("clanPoints", 0)
        }
        
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            donations[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"]
            }
    
    save_donations(donations)
    return donations

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Clash Donations</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .header { background: #e74c3c; color: white; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        .section { background: white; margin: 20px 0; padding: 20px; border-radius: 5px; }
        select { width: 100%; padding: 10px; margin: 10px 0; }
        .player { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }
        .player:nth-child(even) { background: #f9f9f9; }
    </style>
</head>
<body>
    <div class="header"><h1>🏆 Clash Donations Tracker</h1></div>
    <div class="container">
        <div class="section">
            <h3>Select Clan:</h3>
            <select id="clanSelect" onchange="loadClan()">
                <option value="">Loading...</option>
            </select>
        </div>
        <div id="clanData" style="display:none;">
            <div class="section">
                <h2 id="clanName">Clan Name</h2>
                <p>Members: <span id="memberCount">0</span></p>
            </div>
            <div class="section">
                <h3>Players:</h3>
                <div id="playersList">Loading...</div>
            </div>
        </div>
    </div>
    
    <script>
        let currentData = {};
        
        async function loadClans() {
            try {
                const response = await fetch('/api/clans');
                const clans = await response.json();
                const select = document.getElementById('clanSelect');
                select.innerHTML = '<option value="">Select Clan</option>';
                
                for (const [tag, name] of Object.entries(clans)) {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = name + ' (' + tag + ')';
                    select.appendChild(option);
                }
                
                if (Object.keys(clans).length > 0) {
                    select.value = Object.keys(clans)[0];
                    loadClan();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function loadClan() {
            const select = document.getElementById('clanSelect');
            const clanTag = select.value;
            
            if (!clanTag) {
                document.getElementById('clanData').style.display = 'none';
                return;
            }
            
            try {
                const response = await fetch('/api/clan/' + encodeURIComponent(clanTag));
                const data = await response.json();
                currentData = data;
                
                document.getElementById('clanData').style.display = 'block';
                document.getElementById('clanName').textContent = data.clan_info.name;
                document.getElementById('memberCount').textContent = data.clan_info.members;
                
                const players = Object.values(data.players);
                players.sort((a, b) => b.donations - a.donations);
                
                let html = '';
                players.forEach((player, index) => {
                    html += '<div class="player">';
                    html += '<span>' + (index + 1) + '. ' + player.name + '</span>';
                    html += '<span>Donations: ' + player.donations.toLocaleString() + '</span>';
                    html += '</div>';
                });
                
                document.getElementById('playersList').innerHTML = html;
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('playersList').innerHTML = 'Error loading data';
            }
        }
        
        window.onload = function() {
            loadClans();
            setInterval(loadClan, 5 * 60 * 1000);
        };
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif self.path == "/api/clans":
            clans = load_clans()
            self.send_json(clans)
            
        elif self.path.startswith("/api/clan/"):
            clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
            data = process_donations()
            clan_key = clan_tag.replace("#", "")
            
            if clan_key in data:
                self.send_json(data[clan_key])
            else:
                self.send_json({"error": "Clan not found"})
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        pass

def main():
    print("🚀 Starting Clash of Clans Donations Server...")
    print(f"🌐 URL: http://localhost:{PORT}")
    
    if not os.path.exists("clans.json"):
        save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
    
    if not os.path.exists("donations.json"):
        save_donations({})
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ Server running on http://localhost:{PORT}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ Error: Port {PORT} is busy. Kill existing process:")
        print("pkill -f python")
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
rm clash_server.py
nano clash_server.py

#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import threading
import time
from datetime import datetime

PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

def load_clans():
    if os.path.exists("clans.json"):
        with open("clans.json", "r") as f:
            return json.load(f)
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def save_clans(clans):
    with open("clans.json", "w") as f:
        json.dump(clans, f, indent=2)

def load_donations():
    if os.path.exists("donations.json"):
        with open("donations.json", "r") as f:
            return json.load(f)
    return {}

def save_donations(data):
    with open("donations.json", "w") as f:
        json.dump(data, f, indent=2)

def get_clan_data(clan_tag):
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe="")
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_KEY}")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_donations():
    donations = load_donations()
    clans = load_clans()
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        
        if clan_key not in donations:
            donations[clan_key] = {
                "clan_info": {},
                "players": {}
            }
        
        donations[clan_key]["clan_info"] = {
            "name": clan_data.get("name", ""),
            "members": clan_data.get("members", 0),
            "points": clan_data.get("clanPoints", 0)
        }
        
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            donations[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"]
            }
    
    save_donations(donations)
    return donations

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 Clash Donations Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .card {
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-weight: 500;
            margin-bottom: 8px;
            color: #495057;
        }
        
        select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            background: white;
            transition: border-color 0.2s ease;
        }
        
        select:focus {
            outline: none;
            border-color: #e74c3c;
            box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
        }
        
        .clan-info {
            text-align: center;
            padding: 30px 0;
        }
        
        .clan-name {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        
        .member-count {
            font-size: 1.1rem;
            color: #6c757d;
        }
        
        .loading-state {
            text-align: center;
            padding: 40px 20px;
        }
        
        .loading-text {
            font-size: 1.1rem;
            color: #6c757d;
        }
        
        .players-section {
            margin-top: 10px;
        }
        
        .players-header {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .player-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .player-item:last-child {
            border-bottom: none;
        }
        
        .player-rank {
            font-weight: 600;
            color: #e74c3c;
            margin-right: 12px;
            min-width: 30px;
        }
        
        .player-name {
            flex: 1;
            font-weight: 500;
        }
        
        .player-donations {
            font-weight: 600;
            color: #28a745;
        }
        
        .error-state {
            text-align: center;
            padding: 40px 20px;
            color: #dc3545;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
                margin: 0;
            }
            
            .card {
                margin: 10px 0;
                padding: 20px;
                border-radius: 8px;
            }
            
            .loading-number {
                font-size: 6rem;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Clash Donations Tracker</h1>
    </div>
    
    <div class="container">
        <div class="card">
            <div class="form-group">
                <label for="clanSelect">Select Clan:</label>
                <select id="clanSelect" onchange="loadClan()">
                    <option value="">Loading clans...</option>
                </select>
            </div>
        </div>
        
        <div id="clanData" style="display:none;">
            <div class="card">
                <div class="clan-info">
                    <div class="clan-name" id="clanName">Clan Name</div>
                    <div class="member-count">Members: <span id="memberCount">0</span></div>
                </div>
            </div>
            
            <div class="card">
                <div class="players-section">
                    <div class="players-header">Players:</div>
                    <div id="playersList">
                        <div class="loading-state">
                            <div class="loading-text">Error loading data</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="initialLoading" class="card">
            <div class="loading-state">
                <div class="loading-text">Loading clan data...</div>
            </div>
        </div>
    </div>
    
    <script>
        let currentData = {};
        
        async function loadClans() {
            try {
                const response = await fetch('/api/clans');
                const clans = await response.json();
                const select = document.getElementById('clanSelect');
                
                select.innerHTML = '<option value="">Select Clan</option>';
                
                for (const [tag, name] of Object.entries(clans)) {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = `${name} (${tag})`;
                    select.appendChild(option);
                }
                
                // Auto-select first clan if available
                if (Object.keys(clans).length > 0) {
                    const firstClanTag = Object.keys(clans)[0];
                    select.value = firstClanTag;
                    loadClan();
                } else {
                    document.getElementById('initialLoading').style.display = 'none';
                }
                
            } catch (error) {
                console.error('Error loading clans:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading clan data</div>';
            }
        }
        
        async function loadClan() {
            const select = document.getElementById('clanSelect');
            const clanTag = select.value;
            
            if (!clanTag) {
                document.getElementById('clanData').style.display = 'none';
                document.getElementById('initialLoading').style.display = 'block';
                return;
            }
            
            // Hide initial loading and show clan data section
            document.getElementById('initialLoading').style.display = 'none';
            document.getElementById('clanData').style.display = 'block';
            
            // Show loading state for players
            document.getElementById('playersList').innerHTML = 
                '<div class="loading-state"><div class="loading-text">Loading players...</div></div>';
            
            try {
                const response = await fetch('/api/clan/' + encodeURIComponent(clanTag));
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                currentData = data;
                
                // Update clan info
                document.getElementById('clanName').textContent = data.clan_info.name || 'Unknown Clan';
                document.getElementById('memberCount').textContent = data.clan_info.members || 0;
                
                // Sort and display players
                const players = Object.values(data.players || {});
                players.sort((a, b) => (b.donations || 0) - (a.donations || 0));
                
                if (players.length === 0) {
                    document.getElementById('playersList').innerHTML = 
                        '<div class="loading-state"><div class="loading-text">No players found</div></div>';
                    return;
                }
                
                let html = '';
                players.forEach((player, index) => {
                    html += `
                        <div class="player-item">
                            <span class="player-rank">${index + 1}.</span>
                            <span class="player-name">${player.name || 'Unknown'}</span>
                            <span class="player-donations">${(player.donations || 0).toLocaleString()}</span>
                        </div>
                    `;
                });
                
                document.getElementById('playersList').innerHTML = html;
                
            } catch (error) {
                console.error('Error loading clan data:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading players data</div>';
            }
        }
        
        // Initialize app
        window.addEventListener('load', function() {
            loadClans();
            
            // Auto-refresh every 5 minutes
            setInterval(() => {
                if (document.getElementById('clanSelect').value) {
                    loadClan();
                }
            }, 5 * 60 * 1000);
        });
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif self.path == "/api/clans":
            clans = load_clans()
            self.send_json(clans)
            
        elif self.path.startswith("/api/clan/"):
            clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
            data = process_donations()
            clan_key = clan_tag.replace("#", "")
            
            if clan_key in data:
                self.send_json(data[clan_key])
            else:
                self.send_json({"error": "Clan not found"})
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        # Suppress server logs for cleaner output
        pass

def main():
    print("🚀 Starting Clash of Clans Donations Server...")
    print(f"🌐 URL: http://localhost:{PORT}")
    
    # Ensure required files exist
    if not os.path.exists("clans.json"):
        save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
        print("📝 Created default clans.json file")
    
    if not os.path.exists("donations.json"):
        save_donations({})
        print("📝 Created donations.json file")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ Server running on http://localhost:{PORT}")
            print("📱 Open the URL in your mobile browser")
            print("🔄 Data auto-refreshes every 5 minutes")
            print("❌ Press Ctrl+C to stop")
            print("-" * 50)
            httpd.serve_forever()
            
    except OSError as e:
        print(f"❌ Error: Port {PORT} is busy.")
        print("💡 Try killing existing processes:")
        print("   pkill -f python")
        print(f"   lsof -ti:{PORT} | xargs kill -9")
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")
        print("💾 Data saved to JSON files")

if __name__ == "__main__":
    main()

rm clash_server.py
nano clash_server.py
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import time
from datetime import datetime

PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

def load_clans():
    if os.path.exists("clans.json"):
        try:
            with open("clans.json", "r") as f:
                return json.load(f)
        except:
            pass
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def save_clans(clans):
    try:
        with open("clans.json", "w") as f:
            json.dump(clans, f, indent=2)
    except Exception as e:
        print(f"Error saving clans: {e}")

def load_donations():
    if os.path.exists("donations.json"):
        try:
            with open("donations.json", "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_donations(data):
    try:
        with open("donations.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving donations: {e}")

def get_clan_data(clan_tag):
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe="")
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_KEY}")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error getting clan data: {e}")
        return None

def process_donations():
    donations = load_donations()
    clans = load_clans()
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        
        if clan_key not in donations:
            donations[clan_key] = {
                "clan_info": {},
                "players": {}
            }
        
        donations[clan_key]["clan_info"] = {
            "name": clan_data.get("name", ""),
            "members": clan_data.get("members", 0),
            "points": clan_data.get("clanPoints", 0)
        }
        
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            donations[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"]
            }
    
    save_donations(donations)
    return donations

# HTML corregido con comillas simples
HTML_PAGE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clash Donations Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .card {
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-weight: 500;
            margin-bottom: 8px;
            color: #495057;
        }
        
        select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            background: white;
            transition: border-color 0.2s ease;
        }
        
        select:focus {
            outline: none;
            border-color: #e74c3c;
            box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
        }
        
        .clan-info {
            text-align: center;
            padding: 30px 0;
        }
        
        .clan-name {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        
        .member-count {
            font-size: 1.1rem;
            color: #6c757d;
        }
        
        .loading-state {
            text-align: center;
            padding: 40px 20px;
        }
        
        .loading-text {
            font-size: 1.1rem;
            color: #6c757d;
        }
        
        .players-section {
            margin-top: 10px;
        }
        
        .players-header {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .player-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .player-item:last-child {
            border-bottom: none;
        }
        
        .player-rank {
            font-weight: 600;
            color: #e74c3c;
            margin-right: 12px;
            min-width: 30px;
        }
        
        .player-name {
            flex: 1;
            font-weight: 500;
        }
        
        .player-donations {
            font-weight: 600;
            color: #28a745;
        }
        
        .error-state {
            text-align: center;
            padding: 40px 20px;
            color: #dc3545;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
                margin: 0;
            }
            
            .card {
                margin: 10px 0;
                padding: 20px;
                border-radius: 8px;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Clash Donations Tracker</h1>
    </div>
    
    <div class="container">
        <div class="card">
            <div class="form-group">
                <label for="clanSelect">Select Clan:</label>
                <select id="clanSelect" onchange="loadClan()">
                    <option value="">Loading clans...</option>
                </select>
            </div>
        </div>
        
        <div id="clanData" style="display:none;">
            <div class="card">
                <div class="clan-info">
                    <div class="clan-name" id="clanName">Clan Name</div>
                    <div class="member-count">Members: <span id="memberCount">0</span></div>
                </div>
            </div>
            
            <div class="card">
                <div class="players-section">
                    <div class="players-header">Players:</div>
                    <div id="playersList">
                        <div class="loading-state">
                            <div class="loading-text">Error loading data</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="initialLoading" class="card">
            <div class="loading-state">
                <div class="loading-text">Loading clan data...</div>
            </div>
        </div>
    </div>
    
    <script>
        let currentData = {};
        
        async function loadClans() {
            try {
                const response = await fetch('/api/clans');
                const clans = await response.json();
                const select = document.getElementById('clanSelect');
                
                select.innerHTML = '<option value="">Select Clan</option>';
                
                for (const [tag, name] of Object.entries(clans)) {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = name + ' (' + tag + ')';
                    select.appendChild(option);
                }
                
                if (Object.keys(clans).length > 0) {
                    const firstClanTag = Object.keys(clans)[0];
                    select.value = firstClanTag;
                    loadClan();
                } else {
                    document.getElementById('initialLoading').style.display = 'none';
                }
                
            } catch (error) {
                console.error('Error loading clans:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading clan data</div>';
            }
        }
        
        async function loadClan() {
            const select = document.getElementById('clanSelect');
            const clanTag = select.value;
            
            if (!clanTag) {
                document.getElementById('clanData').style.display = 'none';
                document.getElementById('initialLoading').style.display = 'block';
                return;
            }
            
            document.getElementById('initialLoading').style.display = 'none';
            document.getElementById('clanData').style.display = 'block';
            
            document.getElementById('playersList').innerHTML = 
                '<div class="loading-state"><div class="loading-text">Loading players...</div></div>';
            
            try {
                const response = await fetch('/api/clan/' + encodeURIComponent(clanTag));
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                currentData = data;
                
                document.getElementById('clanName').textContent = data.clan_info.name || 'Unknown Clan';
                document.getElementById('memberCount').textContent = data.clan_info.members || 0;
                
                const players = Object.values(data.players || {});
                players.sort(function(a, b) {
                    return (b.donations || 0) - (a.donations || 0);
                });
                
                if (players.length === 0) {
                    document.getElementById('playersList').innerHTML = 
                        '<div class="loading-state"><div class="loading-text">No players found</div></div>';
                    return;
                }
                
                let html = '';
                players.forEach(function(player, index) {
                    html += '<div class="player-item">';
                    html += '<span class="player-rank">' + (index + 1) + '.</span>';
                    html += '<span class="player-name">' + (player.name || 'Unknown') + '</span>';
                    html += '<span class="player-donations">' + ((player.donations || 0).toLocaleString()) + '</span>';
                    html += '</div>';
                });
                
                document.getElementById('playersList').innerHTML = html;
                
            } catch (error) {
                console.error('Error loading clan data:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading players data</div>';
            }
        }
        
        window.addEventListener('load', function() {
            loadClans();
            
            setInterval(function() {
                if (document.getElementById('clanSelect').value) {
                    loadClan();
                }
            }, 5 * 60 * 1000);
        });
    </script>
</body>
</html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(HTML_PAGE.encode('utf-8'))
                
            elif self.path == "/api/clans":
                clans = load_clans()
                self.send_json(clans)
                
            elif self.path.startswith("/api/clan/"):
                clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
                data = process_donations()
                clan_key = clan_tag.replace("#", "")
                
                if clan_key in data:
                    self.send_json(data[clan_key])
                else:
                    self.send_json({"error": "Clan not found"})
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"Request error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def send_json(self, data):
        try:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        except Exception as e:
            print(f"JSON response error: {e}")
    
    def log_message(self, format, *args):
        pass

def main():
    print("🚀 Starting Clash of Clans Server...")
    print(f"📱 URL: http://localhost:{PORT}")
    
    try:
        if not os.path.exists("clans.json"):
            save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
            print("✅ Created clans.json")
        
        if not os.path.exists("donations.json"):
            save_donations({})
            print("✅ Created donations.json")
        
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ Server running on port {PORT}")
            print("❌ Press Ctrl+C to stop")
            httpd.serve_forever()
            
    except OSError:
        print(f"❌ Port {PORT} busy. Try: pkill -f python")
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
rm clash_server.py
nano clash_server.py
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os

PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

def load_clans():
    try:
        if os.path.exists("clans.json"):
            with open("clans.json", "r") as f:
                return json.load(f)
    except:
        pass
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def save_clans(clans):
    try:
        with open("clans.json", "w") as f:
            json.dump(clans, f, indent=2)
    except:
        pass

def load_donations():
    try:
        if os.path.exists("donations.json"):
            with open("donations.json", "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_donations(data):
    try:
        with open("donations.json", "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def get_clan_data(clan_tag):
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe="")
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_KEY}")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except:
        return None

def process_donations():
    donations = load_donations()
    clans = load_clans()
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        
        if clan_key not in donations:
            donations[clan_key] = {
                "clan_info": {},
                "players": {}
            }
        
        donations[clan_key]["clan_info"] = {
            "name": clan_data.get("name", ""),
            "members": clan_data.get("members", 0),
            "points": clan_data.get("clanPoints", 0)
        }
        
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            donations[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"]
            }
    
    save_donations(donations)
    return donations

def get_html():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clash Donations Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background: #f8f9fa;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 1.8rem;
            margin: 0;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .card {
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
            color: #495057;
        }
        
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            background: white;
        }
        
        select:focus {
            outline: none;
            border-color: #e74c3c;
        }
        
        .clan-info {
            text-align: center;
            padding: 20px 0;
        }
        
        .clan-name {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        
        .member-count {
            font-size: 1.1rem;
            color: #6c757d;
        }
        
        .loading-text {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        
        .players-header {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .player-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .player-rank {
            font-weight: bold;
            color: #e74c3c;
            margin-right: 12px;
            min-width: 30px;
        }
        
        .player-name {
            flex: 1;
            font-weight: 500;
        }
        
        .player-donations {
            font-weight: bold;
            color: #28a745;
        }
        
        .error-state {
            text-align: center;
            padding: 40px;
            color: #dc3545;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .card {
                margin: 10px 0;
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Clash Donations Tracker</h1>
    </div>
    
    <div class="container">
        <div class="card">
            <label for="clanSelect">Select Clan:</label>
            <select id="clanSelect" onchange="loadClan()">
                <option value="">Loading...</option>
            </select>
        </div>
        
        <div id="clanData" style="display:none;">
            <div class="card">
                <div class="clan-info">
                    <div class="clan-name" id="clanName">Clan Name</div>
                    <div class="member-count">Members: <span id="memberCount">0</span></div>
                </div>
            </div>
            
            <div class="card">
                <div class="players-header">Players:</div>
                <div id="playersList">
                    <div class="loading-text">Loading...</div>
                </div>
            </div>
        </div>
        
        <div id="initialLoading" class="card">
            <div class="loading-text">Loading clan data...</div>
        </div>
    </div>
    
    <script>
        function loadClans() {
            fetch('/api/clans')
            .then(function(response) {
                return response.json();
            })
            .then(function(clans) {
                var select = document.getElementById('clanSelect');
                select.innerHTML = '<option value="">Select Clan</option>';
                
                for (var tag in clans) {
                    var option = document.createElement('option');
                    option.value = tag;
                    option.textContent = clans[tag] + ' (' + tag + ')';
                    select.appendChild(option);
                }
                
                if (Object.keys(clans).length > 0) {
                    var firstTag = Object.keys(clans)[0];
                    select.value = firstTag;
                    loadClan();
                } else {
                    document.getElementById('initialLoading').style.display = 'none';
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading data</div>';
            });
        }
        
        function loadClan() {
            var select = document.getElementById('clanSelect');
            var clanTag = select.value;
            
            if (!clanTag) {
                document.getElementById('clanData').style.display = 'none';
                document.getElementById('initialLoading').style.display = 'block';
                return;
            }
            
            document.getElementById('initialLoading').style.display = 'none';
            document.getElementById('clanData').style.display = 'block';
            document.getElementById('playersList').innerHTML = 
                '<div class="loading-text">Loading players...</div>';
            
            fetch('/api/clan/' + encodeURIComponent(clanTag))
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                document.getElementById('clanName').textContent = data.clan_info.name || 'Unknown';
                document.getElementById('memberCount').textContent = data.clan_info.members || 0;
                
                var players = [];
                for (var tag in data.players) {
                    players.push(data.players[tag]);
                }
                
                players.sort(function(a, b) {
                    return (b.donations || 0) - (a.donations || 0);
                });
                
                if (players.length === 0) {
                    document.getElementById('playersList').innerHTML = 
                        '<div class="loading-text">No players found</div>';
                    return;
                }
                
                var html = '';
                for (var i = 0; i < players.length; i++) {
                    var player = players[i];
                    html += '<div class="player-item">';
                    html += '<span class="player-rank">' + (i + 1) + '.</span>';
                    html += '<span class="player-name">' + (player.name || 'Unknown') + '</span>';
                    html += '<span class="player-donations">' + (player.donations || 0).toLocaleString() + '</span>';
                    html += '</div>';
                }
                
                document.getElementById('playersList').innerHTML = html;
            })
            .catch(function(error) {
                console.error('Error:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading players</div>';
            });
        }
        
        window.addEventListener('load', function() {
            loadClans();
            setInterval(function() {
                if (document.getElementById('clanSelect').value) {
                    loadClan();
                }
            }, 300000);
        });
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(get_html().encode())
                
            elif self.path == "/api/clans":
                clans = load_clans()
                self.send_json(clans)
                
            elif self.path.startswith("/api/clan/"):
                clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
                data = process_donations()
                clan_key = clan_tag.replace("#", "")
                
                if clan_key in data:
                    self.send_json(data[clan_key])
                else:
                    self.send_json({"error": "Clan not found"})
            else:
                self.send_response(404)
                self.end_headers()
        except:
            self.send_response(500)
            self.end_headers()
    
    def send_json(self, data):
        try:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except:
            pass
    
    def log_message(self, format, *args):
        pass

def main():
    print("🚀 Starting server...")
    print(f"📱 Open: http://localhost:{PORT}")
    
    if not os.path.exists("clans.json"):
        save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
        print("✅ Created clans.json")
    
    if not os.path.exists("donations.json"):
        save_donations({})
        print("✅ Created donations.json")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("✅ Server running!")
            print("❌ Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError:
        print(f"❌ Port {PORT} busy")
    except KeyboardInterrupt:
        print("\n👋 Stopped")

if __name__ == "__main__":
    main()

rm clash_server.py
nano clash_server.py
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os

PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

def load_clans():
    try:
        if os.path.exists("clans.json"):
            with open("clans.json", "r") as f:
                return json.load(f)
    except:
        pass
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def save_clans(clans):
    try:
        with open("clans.json", "w") as f:
            json.dump(clans, f, indent=2)
    except:
        pass

def load_donations():
    try:
        if os.path.exists("donations.json"):
            with open("donations.json", "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_donations(data):
    try:
        with open("donations.json", "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def get_clan_data(clan_tag):
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe="")
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_KEY}")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except:
        return None

def process_donations():
    donations = load_donations()
    clans = load_clans()
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        
        if clan_key not in donations:
            donations[clan_key] = {
                "clan_info": {},
                "players": {},
                "daily_donations": {}
            }
        
        donations[clan_key]["clan_info"] = {
            "name": clan_data.get("name", ""),
            "members": clan_data.get("members", 0),
            "points": clan_data.get("clanPoints", 0)
        }
        
        # Store total donations
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            donations[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"]
            }
    
    save_donations(donations)
    return donations

def get_html():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TOP REQ CLANS</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.4;
        }
        
        .header {
            background: #e74c3c;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
            background: white;
            min-height: calc(100vh - 60px);
        }
        
        .clan-selector {
            padding: 20px;
            border-bottom: 1px solid #eee;
        }
        
        .clan-selector label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
        
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
            background: white;
            color: #333;
        }
        
        .clan-info {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        .clan-name {
            font-size: 1.3rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .member-count {
            color: #666;
            font-size: 0.9rem;
        }
        
        .donation-tabs {
            display: flex;
            border-bottom: 1px solid #eee;
        }
        
        .tab-button {
            flex: 1;
            padding: 15px;
            background: white;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            border-bottom: 2px solid transparent;
        }
        
        .tab-button.active {
            color: #e74c3c;
            border-bottom-color: #e74c3c;
        }
        
        .players-list {
            padding: 0;
        }
        
        .player-item {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .player-rank {
            min-width: 30px;
            font-weight: 600;
            color: #666;
            font-size: 14px;
        }
        
        .player-name {
            flex: 1;
            margin-left: 10px;
            font-weight: 500;
            color: #333;
        }
        
        .player-donations {
            font-weight: 600;
            color: #28a745;
            font-size: 14px;
        }
        
        .loading-state {
            padding: 40px 20px;
            text-align: center;
            color: #666;
        }
        
        .error-state {
            padding: 40px 20px;
            text-align: center;
            color: #e74c3c;
        }
        
        .no-data {
            padding: 40px 20px;
            text-align: center;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="header">
        🏆 TOP REQ CLANS
    </div>
    
    <div class="container">
        <div class="clan-selector">
            <label for="clanSelect">Select Clan:</label>
            <select id="clanSelect" onchange="loadClan()">
                <option value="">Loading...</option>
            </select>
        </div>
        
        <div id="clanContent" style="display:none;">
            <div class="clan-info">
                <div class="clan-name" id="clanName">Clan Name</div>
                <div class="member-count">Members: <span id="memberCount">0</span></div>
            </div>
            
            <div class="donation-tabs">
                <button class="tab-button active" onclick="showTab('daily')" id="dailyTab">
                    Daily Donations
                </button>
                <button class="tab-button" onclick="showTab('total')" id="totalTab">
                    Total Donations
                </button>
            </div>
            
            <div class="players-list" id="playersList">
                <div class="loading-state">Loading players...</div>
            </div>
        </div>
        
        <div id="loadingState" class="loading-state">
            Loading clan data...
        </div>
    </div>
    
    <script>
        var currentData = {};
        var currentTab = 'daily';
        
        function loadClans() {
            fetch('/api/clans')
            .then(function(response) {
                return response.json();
            })
            .then(function(clans) {
                var select = document.getElementById('clanSelect');
                select.innerHTML = '';
                
                for (var tag in clans) {
                    var option = document.createElement('option');
                    option.value = tag;
                    option.textContent = clans[tag] + ' (' + tag + ')';
                    select.appendChild(option);
                }
                
                if (Object.keys(clans).length > 0) {
                    var firstTag = Object.keys(clans)[0];
                    select.value = firstTag;
                    loadClan();
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading clans</div>';
            });
        }
        
        function loadClan() {
            var select = document.getElementById('clanSelect');
            var clanTag = select.value;
            
            if (!clanTag) {
                document.getElementById('clanContent').style.display = 'none';
                document.getElementById('loadingState').style.display = 'block';
                return;
            }
            
            document.getElementById('loadingState').style.display = 'none';
            document.getElementById('clanContent').style.display = 'block';
            document.getElementById('playersList').innerHTML = 
                '<div class="loading-state">Loading players...</div>';
            
            fetch('/api/clan/' + encodeURIComponent(clanTag))
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                currentData = data;
                
                document.getElementById('clanName').textContent = data.clan_info.name || 'Unknown Clan';
                document.getElementById('memberCount').textContent = data.clan_info.members || 0;
                
                showPlayersList();
            })
            .catch(function(error) {
                console.error('Error:', error);
                document.getElementById('playersList').innerHTML = 
                    '<div class="error-state">Error loading players data</div>';
            });
        }
        
        function showTab(tabName) {
            currentTab = tabName;
            
            document.getElementById('dailyTab').classList.remove('active');
            document.getElementById('totalTab').classList.remove('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            showPlayersList();
        }
        
        function showPlayersList() {
            if (!currentData.players) {
                document.getElementById('playersList').innerHTML = 
                    '<div class="no-data">No player data available</div>';
                return;
            }
            
            var players = [];
            for (var tag in currentData.players) {
                players.push(currentData.players[tag]);
            }
            
            // Sort by donations
            players.sort(function(a, b) {
                return (b.donations || 0) - (a.donations || 0);
            });
            
            if (players.length === 0) {
                document.getElementById('playersList').innerHTML = 
                    '<div class="no-data">No players found</div>';
                return;
            }
            
            var html = '';
            for (var i = 0; i < players.length; i++) {
                var player = players[i];
                var donations = currentTab === 'daily' ? 
                    (player.donations || 0) : (player.donations || 0);
                
                html += '<div class="player-item">';
                html += '<span class="player-rank">' + (i + 1) + '.</span>';
                html += '<span class="player-name">' + (player.name || 'Unknown') + '</span>';
                html += '<span class="player-donations">' + donations.toLocaleString() + '</span>';
                html += '</div>';
            }
            
            document.getElementById('playersList').innerHTML = html;
        }
        
        window.addEventListener('load', function() {
            loadClans();
            
            setInterval(function() {
                if (document.getElementById('clanSelect').value) {
                    loadClan();
                }
            }, 300000);
        });
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(get_html().encode())
                
            elif self.path == "/api/clans":
                clans = load_clans()
                self.send_json(clans)
                
            elif self.path.startswith("/api/clan/"):
                clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
                data = process_donations()
                clan_key = clan_tag.replace("#", "")
                
                if clan_key in data:
                    self.send_json(data[clan_key])
                else:
                    self.send_json({"error": "Clan not found"})
            else:
                self.send_response(404)
                self.end_headers()
        except:
            self.send_response(500)
            self.end_headers()
    
    def send_json(self, data):
        try:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except:
            pass
    
    def log_message(self, format, *args):
        pass

def main():
    print("🚀 Starting TOP REQ CLANS...")
    print(f"📱 Open: http://localhost:{PORT}")
    
    if not os.path.exists("clans.json"):
        save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
        print("✅ Created clans.json")
    
    if not os.path.exists("donations.json"):
        save_donations({})
        print("✅ Created donations.json")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("✅ Server running!")
            print("❌ Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError:
        print(f"❌ Port {PORT} busy")
    except KeyboardInterrupt:
        print("\n👋 Stopped")

if __name__ == "__main__":
    main()
