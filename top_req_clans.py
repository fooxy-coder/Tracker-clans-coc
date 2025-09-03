#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os

PORT = 3001

def load_clans():
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def get_clan_data(clan_tag):
    # Simulamos datos para testing
    return {
        "name": "REQUEST & LEAVE",
        "members": 50,
        "memberList": [
            {"tag": "#PLAYER1", "name": "Player 1", "donations": 1500, "donationsReceived": 800, "trophies": 5000},
            {"tag": "#PLAYER2", "name": "Player 2", "donations": 1200, "donationsReceived": 600, "trophies": 4800},
            {"tag": "#PLAYER3", "name": "Player 3", "donations": 1000, "donationsReceived": 400, "trophies": 4500}
        ]
    }

def process_donations():
    clans = load_clans()
    result = {}
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        result[clan_key] = {
            "clan_info": {
                "name": clan_data.get("name", ""),
                "members": clan_data.get("members", 0)
            },
            "players": {}
        }
        
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            result[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"]
            }
    
    return result

HTML_PAGE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TOP REQ CLANS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
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
        
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        
        .clan-info {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        .clan-name {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 5px;
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
            color: #666;
            border-bottom: 2px solid transparent;
        }
        
        .tab-button.active {
            color: #e74c3c;
            border-bottom-color: #e74c3c;
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
        }
        
        .player-name {
            flex: 1;
            margin-left: 10px;
            font-weight: 500;
        }
        
        .player-donations {
            font-weight: 600;
            color: #28a745;
        }
    </style>
</head>
<body>
    <div class="header">🏆 TOP REQ CLANS</div>
    
    <div class="container">
        <div class="clan-selector">
            <select id="clanSelect" onchange="loadClan()">
                <option value="">Loading...</option>
            </select>
        </div>
        
        <div id="clanContent" style="display:none;">
            <div class="clan-info">
                <div class="clan-name" id="clanName">Clan Name</div>
                <div>Members: <span id="memberCount">0</span></div>
            </div>
            
            <div class="donation-tabs">
                <button class="tab-button active" onclick="showTab('daily')" id="dailyTab">
                    Daily Donations
                </button>
                <button class="tab-button" onclick="showTab('total')" id="totalTab">
                    Total Donations
                </button>
            </div>
            
            <div id="playersList"></div>
        </div>
    </div>
    
    <script>
        var currentData = {};
        
        function loadClans() {
            fetch('/api/clans')
            .then(function(response) { return response.json(); })
            .then(function(clans) {
                var select = document.getElementById('clanSelect');
                select.innerHTML = '';
                
                for (var tag in clans) {
                    var option = document.createElement('option');
                    option.value = tag;
                    option.textContent = clans[tag];
                    select.appendChild(option);
                }
                
                if (Object.keys(clans).length > 0) {
                    select.value = Object.keys(clans)[0];
                    loadClan();
                }
            });
        }
        
        function loadClan() {
            var clanTag = document.getElementById('clanSelect').value;
            if (!clanTag) return;
            
            document.getElementById('clanContent').style.display = 'block';
            
            fetch('/api/clan/' + encodeURIComponent(clanTag))
            .then(function(response) { return response.json(); })
            .then(function(data) {
                currentData = data;
                document.getElementById('clanName').textContent = data.clan_info.name;
                document.getElementById('memberCount').textContent = data.clan_info.members;
                showPlayersList();
            });
        }
        
        function showTab(tabName) {
            document.getElementById('dailyTab').classList.remove('active');
            document.getElementById('totalTab').classList.remove('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
            showPlayersList();
        }
        
        function showPlayersList() {
            var players = [];
            for (var tag in currentData.players) {
                players.push(currentData.players[tag]);
            }
            
            players.sort(function(a, b) {
                return (b.donations || 0) - (a.donations || 0);
            });
            
            var html = '';
            for (var i = 0; i < players.length; i++) {
                var player = players[i];
                html += '<div class="player-item">';
                html += '<span class="player-rank">' + (i + 1) + '.</span>';
                html += '<span class="player-name">' + player.name + '</span>';
                html += '<span class="player-donations">' + player.donations + '</span>';
                html += '</div>';
            }
            
            document.getElementById('playersList').innerHTML = html;
        }
        
        window.onload = function() { loadClans(); };
    </script>
</body>
</html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
            
        elif self.path == "/api/clans":
            clans = load_clans()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(clans).encode())
            
        elif self.path.startswith("/api/clan/"):
            clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
            data = process_donations()
            clan_key = clan_tag.replace("#", "")
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            if clan_key in data:
                self.wfile.write(json.dumps(data[clan_key]).encode())
            else:
                self.wfile.write(json.dumps({"error": "Clan not found"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def main():
    print("🚀 Starting TOP REQ CLANS...")
    print(f"📱 Open: http://localhost:{PORT}")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("✅ Server running!")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped")

if __name__ == "__main__":
    main()

rm clash_server.py
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import socket
from datetime import datetime, timezone, timedelta

# Función para encontrar un puerto libre
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

PORT = find_free_port()

def load_clans():
    return {
        "#2LJULC0Q": "REQUEST & LEAVE",
        "#2L39P0GJL": "req", 
        "#LQ9GZ2J9": "Req and Leave",
        "#PZ42ZK0U": "Req n Leave",
        "#2L989PUPG": "Req and leave",
        "#899VUPLL": "TROPAS 0800",
        "#YY2L0YQL": "REQUEST N LEAVE",
        "#G0Q80CR9": "Req",
        "#0LVR0LCC": "Req N Leave",
        "#YGUCPR6G": "Req"
    }

def get_clan_data(clan_tag):
    # Datos simulados más realistas
    clan_data = {
        "#2LJULC0Q": {
            "name": "REQUEST & LEAVE",
            "members": 50,
            "leader": "Kilian™",
            "totalDonations": 21631968,
            "totalReceived": 334867,
            "memberList": [
                {"tag": "#PLAYER1", "name": "Kilian™", "donations": 15000, "donationsReceived": 2800, "trophies": 6200, "dailyDonations": 450},
                {"tag": "#PLAYER2", "name": "Alex", "donations": 12500, "donationsReceived": 3100, "trophies": 5800, "dailyDonations": 380},
                {"tag": "#PLAYER3", "name": "Mario", "donations": 11200, "donationsReceived": 2400, "trophies": 5500, "dailyDonations": 320},
                {"tag": "#PLAYER4", "name": "Luna", "donations": 9800, "donationsReceived": 2900, "trophies": 5200, "dailyDonations": 290},
                {"tag": "#PLAYER5", "name": "Pedro", "donations": 8500, "donationsReceived": 1800, "trophies": 4900, "dailyDonations": 250}
            ]
        }
    }
    
    return clan_data.get(clan_tag, {
        "name": "Clan Name",
        "members": 50,
        "leader": "Leader",
        "totalDonations": 1000000,
        "totalReceived": 50000,
        "memberList": [
            {"tag": "#DEMO1", "name": "Player 1", "donations": 1500, "donationsReceived": 800, "trophies": 5000, "dailyDonations": 50},
            {"tag": "#DEMO2", "name": "Player 2", "donations": 1200, "donationsReceived": 600, "trophies": 4800, "dailyDonations": 45}
        ]
    })

def process_donations():
    clans = load_clans()
    result = {}
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace("#", "")
        result[clan_key] = {
            "clan_info": {
                "name": clan_data.get("name", ""),
                "members": clan_data.get("members", 0),
                "leader": clan_data.get("leader", ""),
                "totalDonations": clan_data.get("totalDonations", 0),
                "totalReceived": clan_data.get("totalReceived", 0)
            },
            "players": {}
        }
        
        for member in clan_data.get("memberList", []):
            player_tag = member["tag"]
            result[clan_key]["players"][player_tag] = {
                "name": member["name"],
                "donations": member.get("donations", 0),
                "received": member.get("donationsReceived", 0),
                "trophies": member["trophies"],
                "dailyDonations": member.get("dailyDonations", 0)
            }
    
    return result

HTML_PAGE = '''<!DOCTYPE html>
<html lang="es">
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: #1a1a1a;
            color: white;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .logo {
            font-size: 18px;
            font-weight: bold;
        }
        
        .logo .top { color: #ff6b35; }
        .logo .req { color: #ff1744; }
        .logo .clans { color: #ff6b35; }
        
        .nav {
            display: flex;
            gap: 20px;
            font-size: 14px;
        }
        
        .nav a {
            color: #ccc;
            text-decoration: none;
            padding: 5px 0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            min-height: calc(100vh - 60px);
        }
        
        .main-view {
            padding: 20px;
        }
        
        .page-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        
        .update-info {
            font-size: 14px;
            color: #666;
            margin-bottom: 20px;
        }
        
        .clans-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .clans-table th {
            background: #f8f9fa;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            font-size: 14px;
            color: #495057;
        }
        
        .clans-table th:first-child {
            width: 40px;
            text-align: center;
        }
        
        .clans-table td {
            padding: 12px;
            border-bottom: 1px solid #f1f1f1;
            vertical-align: middle;
        }
        
        .clans-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .clans-table tr:hover {
            background: #e3f2fd;
            cursor: pointer;
        }
        
        .clan-rank {
            text-align: center;
            font-weight: bold;
            color: #666;
        }
        
        .clan-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .clan-badge {
            width: 32px;
            height: 32px;
            background: #6c5ce7;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
            flex-shrink: 0;
        }
        
        .clan-details h4 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 2px;
            color: #333;
        }
        
        .clan-tag {
            font-size: 11px;
            color: #666;
            font-family: monospace;
        }
        
        .leader-name {
            font-weight: 500;
            color: #333;
        }
        
        .donations-number {
            font-weight: 600;
            color: #2e7d32;
            text-align: right;
        }
        
        .received-number {
            font-weight: 600;
            color: #d32f2f;
            text-align: right;
        }
        
        .clan-detail-view {
            display: none;
            padding: 20px;
        }
        
        .back-button {
            background: #6c5ce7;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .clan-header {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .clan-name {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .clan-stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            font-size: 14px;
            color: #666;
        }
        
        .tab-buttons {
            display: flex;
            margin-bottom: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .tab-button {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .tab-button.active {
            background: #6c5ce7;
            color: white;
        }
        
        .players-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .players-table th {
            background: #f8f9fa;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            font-size: 14px;
        }
        
        .players-table td {
            padding: 12px;
            border-bottom: 1px solid #f1f1f1;
        }
        
        .players-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .player-rank {
            text-align: center;
            font-weight: bold;
            color: #666;
            width: 40px;
        }
        
        .player-name {
            font-weight: 500;
        }
        
        .auto-refresh {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #6c5ce7;
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        @media (max-width: 768px) {
            .nav {
                display: none;
            }
            
            .clans-table, .players-table {
                font-size: 12px;
            }
            
            .clans-table td, .clans-table th,
            .players-table td, .players-table th {
                padding: 8px 6px;
            }
            
            .clan-stats {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">
            <span class="top">TOP</span> <span class="req">REQ</span> <span class="clans">CLANS</span>
        </div>
        <nav class="nav">
            <a href="#" id="levelTab">Level</a>
            <a href="#" id="clansTab" style="color: white;">Clans ▼</a>
            <a href="#" id="playersTab">Players ▼</a>
            <a href="#" id="contactTab">Contact</a>
        </nav>
    </header>

    <div class="container">
        <div class="main-view" id="mainView">
            <h1 class="page-title">Top Req Clans - Current season</h1>
            <p class="update-info">Clan data is updated 24/7! (Last updated: <span id="lastUpdate">Loading...</span>)</p>
            
            <table class="clans-table">
                <thead>
                    <tr>
                        <th></th>
                        <th>Clan</th>
                        <th>Leader</th>
                        <th style="text-align: right;">Total Donate</th>
                        <th style="text-align: right;">Received ▲</th>
                    </tr>
                </thead>
                <tbody id="clansTableBody">
                    <!-- Los clanes se cargarán aquí -->
                </tbody>
            </table>
        </div>
        
        <div class="clan-detail-view" id="clanDetailView">
            <button class="back-button" onclick="showMainView()">← Back to Clans</button>
            
            <div class="clan-header">
                <div class="clan-name" id="detailClanName">Clan Name</div>
                <div class="clan-stats">
                    <span>Leader: <span id="detailLeader">Leader</span></span>
                    <span>Members: <span id="detailMembers">0</span></span>
                    <span>Total Donations: <span id="detailTotalDonations">0</span></span>
                </div>
            </div>
            
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showPlayersTab('total')" id="totalDonationsBtn">
                    Donaciones Totales
                </button>
                <button class="tab-button" onclick="showPlayersTab('daily')" id="dailyDonationsBtn">
                    Donaciones Diarias
                </button>
            </div>
            
            <table class="players-table">
                <thead>
                    <tr>
                        <th></th>
                        <th>Player</th>
                        <th style="text-align: right;">Donaciones</th>
                        <th style="text-align: right;">Recibidas</th>
                        <th style="text-align: right;">Trofeos</th>
                    </tr>
                </thead>
                <tbody id="playersTableBody">
                    <!-- Los jugadores se cargarán aquí -->
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="auto-refresh" id="autoRefresh">
        🔄 Actualizando...
    </div>

    <script>
        var currentData = {};
        var currentView = 'total';
        var selectedClanTag = '';
        var refreshInterval;
        
        function formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(3) + '';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(3) + '';
            }
            return num.toString();
        }
        
        function updateLastUpdateTime() {
            var now = new Date();
            var timeStr = now.getHours().toString().padStart(2, '0') + ':' + 
                         now.getMinutes().toString().padStart(2, '0') + ':' +
                         now.getSeconds().toString().padStart(2, '0');
            document.getElementById('lastUpdate').textContent = 'hace 1 seg';
        }
        
        function loadClans() {
            fetch('/api/clans')
            .then(function(response) { return response.json(); })
            .then(function(clans) {
                var tbody = document.getElementById('clansTableBody');
                tbody.innerHTML = '';
                
                var rank = 1;
                for (var tag in clans) {
                    fetch('/api/clan/' + encodeURIComponent(tag))
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        var row = document.createElement('tr');
                        row.onclick = function() { showClanDetail(tag, data); };
                        
                        var clanInitial = data.clan_info.name.charAt(0);
                        
                        row.innerHTML = 
                            '<td class="clan-rank">' + rank + '.</td>' +
                            '<td class="clan-info">' +
                                '<div class="clan-badge">' + clanInitial + '</div>' +
                                '<div class="clan-details">' +
                                    '<h4>' + data.clan_info.name + '</h4>' +
                                    '<div class="clan-tag">#' + tag + '</div>' +
                                '</div>' +
                            '</td>' +
                            '<td class="leader-name">' + data.clan_info.leader + '</td>' +
                            '<td class="donations-number">' + formatNumber(data.clan_info.totalDonations) + '</td>' +
                            '<td class="received-number">' + formatNumber(data.clan_info.totalReceived) + '</td>';
                        
                        tbody.appendChild(row);
                        rank++;
                    });
                }
                updateLastUpdateTime();
            });
        }
        
        function showClanDetail(clanTag, data) {
            selectedClanTag = clanTag;
            currentData = data;
            
            document.getElementById('mainView').style.display = 'none';
            document.getElementById('clanDetailView').style.display = 'block';
            
            document.getElementById('detailClanName').textContent = data.clan_info.name;
            document.getElementById('detailLeader').textContent = data.clan_info.leader;
            document.getElementById('detailMembers').textContent = data.clan_info.members;
            document.getElementById('detailTotalDonations').textContent = formatNumber(data.clan_info.totalDonations);
            
            showPlayersTab('total');
        }
        
        function showMainView() {
            document.getElementById('mainView').style.display = 'block';
            document.getElementById('clanDetailView').style.display = 'none';
        }
        
        function showPlayersTab(tabType) {
            currentView = tabType;
            
            document.getElementById('totalDonationsBtn').classList.remove('active');
            document.getElementById('dailyDonationsBtn').classList.remove('active');
            document.getElementById(tabType === 'total' ? 'totalDonationsBtn' : 'dailyDonationsBtn').classList.add('active');
            
            var players = [];
            for (var tag in currentData.players) {
                players.push(currentData.players[tag]);
            }
            
            players.sort(function(a, b) {
                var aValue = tabType === 'total' ? (a.donations || 0) : (a.dailyDonations || 0);
                var bValue = tabType === 'total' ? (b.donations || 0) : (b.dailyDonations || 0);
                return bValue - aValue;
            });
            
            var tbody = document.getElementById('playersTableBody');
            tbody.innerHTML = '';
            
            for (var i = 0; i < players.length; i++) {
                var player = players[i];
                var donations = tabType === 'total' ? player.donations : player.dailyDonations;
                
                var row = document.createElement('tr');
                row.innerHTML = 
                    '<td class="player-rank">' + (i + 1) + '.</td>' +
                    '<td class="player-name">' + player.name + '</td>' +
                    '<td style="text-align: right; font-weight: 600; color: #2e7d32;">' + donations + '</td>' +
                    '<td style="text-align: right; font-weight: 600; color: #d32f2f;">' + player.received + '</td>' +
                    '<td style="text-align: right;">' + player.trophies + '</td>';
                
                tbody.appendChild(row);
            }
        }
        
        function resetDailyDonations() {
            var now = new Date();
            var argentina = new Date(now.toLocaleString("en-US", {timeZone: "America/Argentina/Buenos_Aires"}));
            
            if (argentina.getHours() === 2 && argentina.getMinutes() === 0) {
                // Resetear donaciones diarias (esto se haría en el servidor real)
                console.log('Reseteando donaciones diarias...');
            }
        }
        
        function startAutoRefresh() {
            refreshInterval = setInterval(function() {
                if (document.getElementById('mainView').style.display !== 'none') {
                    loadClans();
                } else if (selectedClanTag) {
                    fetch('/api/clan/' + encodeURIComponent(selectedClanTag))
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        currentData = data;
                        showPlayersTab(currentView);
                    });
                }
                resetDailyDonations();
            }, 120000); // 2 minutos
        }
        
        window.onload = function() { 
            loadClans();
            startAutoRefresh();
        };
    </script>
</body>
</html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
            
        elif self.path == "/api/clans":
            clans = load_clans()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(clans).encode())
            
        elif self.path.startswith("/api/clan/"):
            clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
            data = process_donations()
            clan_key = clan_tag.replace("#", "")
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            if clan_key in data:
                self.wfile.write(json.dumps(data[clan_key]).encode())
            else:
                self.wfile.write(json.dumps({"error": "Clan not found"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def main():
    print("🚀 Starting TOP REQ CLANS...")
    print(f"📱 Open: http://localhost:{PORT}")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("✅ Server running!")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped")

if __name__ == "__main__":
    main()
