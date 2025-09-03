#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta
import schedule

# Configuración
PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

# Archivos de datos
CLANS_FILE = "clans.json"
DONATIONS_FILE = "donations_data.json"

# Zona horaria Argentina
ARGENTINA_TZ = timezone(timedelta(hours=-3))

# Cargar clanes desde archivo
def load_clans():
    if os.path.exists(CLANS_FILE):
        with open(CLANS_FILE, 'r') as f:
            return json.load(f)
    return {"#2LJULC0Q": "REQUEST & LEAVE"}  # Clan por defecto

# Guardar clanes
def save_clans(clans):
    with open(CLANS_FILE, 'w') as f:
        json.dump(clans, f, indent=2)

# Cargar datos de donaciones
def load_donations_data():
    if os.path.exists(DONATIONS_FILE):
        with open(DONATIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Guardar datos de donaciones
def save_donations_data(data):
    with open(DONATIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Obtener datos del clan desde la API
def get_clan_data(clan_tag):
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe='')
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {API_KEY}')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error obteniendo datos del clan {clan_tag}: {e}")
        return None

# Procesar donaciones (totales y diarias)
def process_donations():
    donations_data = load_donations_data()
    clans = load_clans()
    current_time = datetime.now(ARGENTINA_TZ)
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace('#', '')
        
        if clan_key not in donations_data:
            donations_data[clan_key] = {
                'clan_info': {},
                'players': {},
                'last_reset': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'last_update': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Actualizar info del clan
        donations_data[clan_key]['clan_info'] = {
            'name': clan_data.get('name', ''),
            'tag': clan_data.get('tag', ''),
            'description': clan_data.get('description', ''),
            'clanLevel': clan_data.get('clanLevel', 0),
            'clanPoints': clan_data.get('clanPoints', 0),
            'members': clan_data.get('members', 0),
            'warWins': clan_data.get('warWins', 0),
            'location': clan_data.get('location', {}).get('name', 'International')
        }
        
        # Procesar miembros
        for member in clan_data.get('memberList', []):
            player_tag = member['tag']
            current_donations = member.get('donations', 0)
            current_received = member.get('donationsReceived', 0)
            
            if player_tag not in donations_data[clan_key]['players']:
                # Nuevo jugador
                donations_data[clan_key]['players'][player_tag] = {
                    'name': member['name'],
                    'role': member['role'],
                    'expLevel': member['expLevel'],
                    'league': member.get('league', {}),
                    'trophies': member['trophies'],
                    'total_donations': current_donations,
                    'total_received': current_received,
                    'daily_donations': 0,
                    'daily_received': 0,
                    'last_donations': current_donations,
                    'last_received': current_received
                }
            else:
                # Jugador existente
                player_data = donations_data[clan_key]['players'][player_tag]
                
                # Calcular donaciones diarias
                daily_donated = current_donations - player_data.get('last_donations', 0)
                daily_received = current_received - player_data.get('last_received', 0)
                
                # Si las donaciones actuales son menores, significa que se reinició
                if current_donations < player_data.get('last_donations', 0):
                    daily_donated = current_donations
                if current_received < player_data.get('last_received', 0):
                    daily_received = current_received
                
                # Actualizar datos
                player_data.update({
                    'name': member['name'],
                    'role': member['role'],
                    'expLevel': member['expLevel'],
                    'league': member.get('league', {}),
                    'trophies': member['trophies'],
                    'total_donations': max(player_data.get('total_donations', 0), current_donations),
                    'total_received': max(player_data.get('total_received', 0), current_received),
                    'daily_donations': player_data.get('daily_donations', 0) + max(0, daily_donated),
                    'daily_received': player_data.get('daily_received', 0) + max(0, daily_received),
                    'last_donations': current_donations,
                    'last_received': current_received
                })
        
        donations_data[clan_key]['last_update'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    save_donations_data(donations_data)
    return donations_data

# Reset diario a las 2 AM
def daily_reset():
    donations_data = load_donations_data()
    current_time = datetime.now(ARGENTINA_TZ)
    
    for clan_key in donations_data:
        for player_tag in donations_data[clan_key]['players']:
            donations_data[clan_key]['players'][player_tag]['daily_donations'] = 0
            donations_data[clan_key]['players'][player_tag]['daily_received'] = 0
        
        donations_data[clan_key]['last_reset'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    save_donations_data(donations_data)
    print(f"Reset diario completado a las {current_time.strftime('%H:%M:%S')}")

# HTML de la página principal
HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top Req Clans - Daily Donations</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(90deg, #ff6b35, #f9ca24);
            color: white;
            padding: 15px 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .clan-selector {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .clan-info {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .donations-summary {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 20px 0;
        }
        
        .total-donations, .total-received {
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
        
        .total-donations {
            background: #27ae60;
        }
        
        .total-received {
            background: #3498db;
        }
        
        .reset-timer {
            text-align: center;
            background: #fff3cd;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }
        
        .tabs {
            display: flex;
            background: white;
            border-radius: 10px 10px 0 0;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border: none;
            background: #ecf0f1;
            font-weight: bold;
        }
        
        .tab.active {
            background: #27ae60;
            color: white;
        }
        
        .players-table {
            background: white;
            border-radius: 0 0 10px 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .table-header {
            display: grid;
            grid-template-columns: 50px 60px 60px 1fr 120px 120px;
            background: #34495e;
            color: white;
            padding: 15px 10px;
            font-weight: bold;
            font-size: 14px;
        }
        
        .player-row {
            display: grid;
            grid-template-columns: 50px 60px 60px 1fr 120px 120px;
            padding: 15px 10px;
            border-bottom: 1px solid #eee;
            align-items: center;
        }
        
        .player-row:nth-child(even) {
            background: #f8f9fa;
        }
        
        .player-rank {
            font-weight: bold;
            text-align: center;
        }
        
        .league-badge {
            width: 40px;
            height: 40px;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            margin: 0 auto;
        }
        
        .player-level {
            background: #3498db;
            color: white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
            margin: 0 auto;
        }
        
        .player-info {
            padding-left: 10px;
        }
        
        .player-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .player-tag {
            font-size: 12px;
            color: #666;
        }
        
        .player-role {
            font-size: 12px;
            color: #e74c3c;
            font-weight: bold;
        }
        
        .donation-number {
            text-align: center;
            font-weight: bold;
            color: #27ae60;
        }
        
        .received-number {
            text-align: center;
            font-weight: bold;
            color: #3498db;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
            font-style: italic;
        }
        
        .error {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }
        
        select {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        @media (max-width: 768px) {
            .table-header, .player-row {
                grid-template-columns: 40px 50px 50px 1fr 80px 80px;
                font-size: 12px;
                padding: 10px 5px;
            }
            
            .donations-summary {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
        }
    </style>
</head>
<body>
    <div class="header">
        🏆 TOP REQ CLANS - Daily Donations
    </div>
    
    <div class="container">
        <div class="clan-selector">
            <h3>Seleccionar Clan:</h3>
            <select id="clanSelect" onchange="loadClanData()">
                <option value="">Cargando clanes...</option>
            </select>
        </div>
        
        <div id="clanInfo" class="clan-info" style="display: none;">
            <div class="clan-header">
                <h2 id="clanName">Cargando...</h2>
                <p id="clanDescription">Descripción del clan</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="totalPoints">0</div>
                    <div class="stat-label">Total Points (Village)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="clanLocation">International</div>
                    <div class="stat-label">Clan Location</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="memberCount">0</div>
                    <div class="stat-label">Members</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="warsWon">0</div>
                    <div class="stat-label">Wars Won</div>
                </div>
            </div>
            
            <div class="reset-timer">
                <strong>Tiempo restante hasta reset de donaciones diarias:</strong> <span id="resetTimer">Calculando...</span>
            </div>
            
            <div class="donations-summary">
                <div class="total-donations">
                    Total Daily Donations: <span id="totalDailyDonations">0</span>
                </div>
                <div class="total-received">
                    Total Daily Received: <span id="totalDailyReceived">0</span>
                </div>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('total')">Total Donations</button>
                <button class="tab" onclick="switchTab('daily')">Daily Donations</button>
            </div>
            
            <div class="players-table">
                <div class="table-header">
                    <div>Rank</div>
                    <div>League</div>
                    <div>Level</div>
                    <div>Player Name</div>
                    <div>Donations ▼</div>
                    <div>Received</div>
                </div>
                <div id="playersContainer">
                    <div class="loading">Cargando datos de jugadores...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentClan = '';
        let currentTab = 'total';
        let clanData = {};
        let clans = {};
        
        // Cargar lista de clanes
        async function loadClans() {
            try {
                const response = await fetch('/api/clans');
                clans = await response.json();
                
                const select = document.getElementById('clanSelect');
                select.innerHTML = '<option value="">Selecciona un clan</option>';
                
                for (const [tag, name] of Object.entries(clans)) {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = `${name} (${tag})`;
                    select.appendChild(option);
                }
                
                // Seleccionar primer clan por defecto
                const firstClan = Object.keys(clans)[0];
                if (firstClan) {
                    select.value = firstClan;
                    loadClanData();
                }
            } catch (error) {
                console.error('Error cargando clanes:', error);
            }
        }
        
        // Cargar datos del clan seleccionado
        async function loadClanData() {
            const select = document.getElementById('clanSelect');
            currentClan = select.value;
            
            if (!currentClan) {
                document.getElementById('clanInfo').style.display = 'none';
                return;
            }
            
            document.getElementById('clanInfo').style.display = 'block';
            document.getElementById('playersContainer').innerHTML = '<div class="loading">Cargando datos...</div>';
            
            try {
                const response = await fetch(`/api/clan/${encodeURIComponent(currentClan)}`);
                clanData = await response.json();
                
                if (clanData.error) {
                    throw new Error(clanData.error);
                }
                
                updateClanInfo();
                updatePlayersTable();
                updateResetTimer();
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('playersContainer').innerHTML = 
                    '<div class="error">Error cargando datos: ' + error.message + '</div>';
            }
        }
        
        // Actualizar información del clan
        function updateClanInfo() {
            const info = clanData.clan_info;
            document.getElementById('clanName').textContent = info.name;
            document.getElementById('clanDescription').textContent = info.description || 'Sin descripción';
            document.getElementById('totalPoints').textContent = info.clanPoints?.toLocaleString() || '0';
            document.getElementById('clanLocation').textContent = info.location || 'International';
            document.getElementById('memberCount').textContent = info.members || '0';
            document.getElementById('warsWon').textContent = info.warWins || '0';
            
            // Calcular totales diarios
            let totalDaily = 0;
            let totalReceived = 0;
            
            Object.values(clanData.players).forEach(player => {
                totalDaily += player.daily_donations || 0;
                totalReceived += player.daily_received || 0;
            });
            
            document.getElementById('totalDailyDonations').textContent = totalDaily.toLocaleString();
            document.getElementById('totalDailyReceived').textContent = totalReceived.toLocaleString();
        }
        
        // Cambiar pestaña
        function switchTab(tab) {
            currentTab = tab;
            
            // Actualizar botones
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`.tab:nth-child(${tab === 'total' ? '1' : '2'})`).classList.add('active');
            
            updatePlayersTable();
        }
        
        // Actualizar tabla de jugadores
        function updatePlayersTable() {
            const players = Object.values(clanData.players);
            
            // Ordenar según la pestaña actual
            players.sort((a, b) => {
                const field = currentTab === 'total' ? 'total_donations' : 'daily_donations';
                return (b[field] || 0) - (a[field] || 0);
            });
            
            let html = '';
            players.forEach((player, index) => {
                const donations = currentTab === 'total' ? (player.total_donations || 0) : (player.daily_donations || 0);
                const received = currentTab === 'total' ? (player.total_received || 0) : (player.daily_received || 0);
                
                html += `
                    <div class="player-row">
                        <div class="player-rank">${index + 1}.</div>
                        <div class="league-badge" style="background-image: url('${getLeagueIcon(player.league)}')"></div>
                        <div class="player-level">${player.expLevel || 1}</div>
                        <div class="player-info">
                            <div class="player-name">${player.name}</div>
                            <div class="player-tag">${player.tag || ''}</div>
                            <div class="player-role">${getRoleText(player.role)}</div>
                        </div>
                        <div class="donation-number">${donations.toLocaleString()}</div>
                        <div class="received-number">${received.toLocaleString()}</div>
                    </div>
                `;
            });
            
            document.getElementById('playersContainer').innerHTML = html;
        }
        
        // Obtener icono de liga
        function getLeagueIcon(league) {
            if (!league || !league.iconUrls) return '';
            return league.iconUrls.small || '';
        }
        
        // Obtener texto de rol
        function getRoleText(role) {
            const roles = {
                'leader': 'Leader',
                'coLeader': 'Co-leader',
                'admin': 'Elder',
                'member': 'Member'
            };
            return roles[role] || 'Member';
        }
        
        // Actualizar timer de reset
        function updateResetTimer() {
            function updateTimer() {
                const now = new Date();
                const argentina = new Date(now.toLocaleString("en-US", {timeZone: "America/Argentina/Buenos_Aires"}));
                
                const nextReset = new Date(argentina);
                nextReset.setHours(2, 0, 0, 0);
                
                if (argentina.getHours() >= 2) {
                    nextReset.setDate(nextReset.getDate() + 1);
                }
                
                const diff = nextReset - argentina;
                const hours = Math.floor(diff / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                
                document.getElementById('resetTimer').textContent = 
                    `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
            
            updateTimer();
            setInterval(updateTimer, 1000);
        }
        
        // Inicializar página
        window.onload = function() {
            loadClans();
            
            // Actualizar datos cada 5 minutos
            setInterval(() => {
                if (currentClan) {
                    loadClanData();
                }
            }, 5 * 60 * 1000);
        };
    </script>
</body>
</html>"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
            
        elif self.path == "/api/clans":
            clans = load_clans()
            self.send_json_response(clans)
            
        elif self.path.startswith("/api/clan/"):
            clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
            donations_data = process_donations()
            
            clan_key = clan_tag.replace('#', '')
            if clan_key in donations_data:
                self.send_json_response(donations_data[clan_key])
            else:
                self.send_json_response({"error": "Clan no encontrado"})
                
        elif self.path == "/api/add-clan":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            add_clan_html = """
            <html><body>
            <h2>Agregar Nuevo Clan</h2>
            <form method="POST" action="/api/add-clan">
                <p>Tag del Clan: <input type="text" name="clan_tag" placeholder="#2LJULC0Q" required></p>
                <p>Nombre del Clan: <input type="text" name="clan_name" placeholder="Mi Clan" required></p>
                <p><button type="submit">Agregar Clan</button></p>
            </form>
            <p><a href="/">Volver</a></p>
            </body></html>
            """
            self.wfile.write(add_clan_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/api/add-clan":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            clan_tag = params.get('clan_tag', [''])[0].strip()
            clan_name = params.get('clan_name', [''])[0].strip()
            
            if clan_tag and clan_name:
                if not clan_tag.startswith('#'):
                    clan_tag = '#' + clan_tag
                    
                clans = load_clans()
                clans[clan_tag] = clan_name
                save_clans(clans)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                success_html = f"""
                <html><body>
                <h2>✅ Clan agregado exitosamente!</h2>
                <p>Clan: {clan_name}</p>
                <p>Tag: {clan_tag}</p>
                <p><a href="/">Ir al dashboard</a></p>
                <p><a href="/api/add-clan">Agregar otro clan</a></p>
                </body></html>
                """
                self.wfile.write(success_html.encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                error_html = """
                <html><body>
                <h2>❌ Error</h2>
                <p>Debes completar todos los campos</p>
                <p><a href="/api/add-clan">Volver</a></p>
                </body></html>
                """
                self.wfile.write(error_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        return  # Silenciar logs

def run_scheduler():
    """Ejecutar el programador de tareas en un hilo separado"""
    schedule.every().day.at("02:00").do(daily_reset)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar cada minuto

def main():
    print("🚀 Iniciando servidor Clash of Clans...")
    print(f"📡 Puerto: {PORT}")
    print(f"🌐 URL: http://localhost:{PORT}")
    print(f"➕ Agregar clanes: http://localhost:{PORT}/api/add-clan")
    print("⏰ Reset diario configurado para las 2:00 AM (Argentina)")
    
    # Crear archivos si no existen
    if not os.path.exists(CLANS_FILE):
        save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
        print(f"✅ Archivo {CLANS_FILE} creado con clan por defecto")
    
    if not os.path.exists(DONATIONS_FILE):
        save_donations_data({})
        print(f"✅ Archivo {DONATIONS_FILE} creado")
    
    # Procesar donaciones inicial
    print("📊 Procesando datos iniciales...")
    process_donations()
    
    # Iniciar programador en hilo separado
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏱️ Programador de reset diario iniciado")
    
    # Iniciar servidor
    try:
        with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
            print(f"✅ Servidor corriendo en http://localhost:{PORT}")
            print("📱 Abre tu navegador y ve a la URL de arriba")
            print("\n🔄 Actualizando datos cada 5 minutos automáticamente")
            print("💾 Los datos se guardan automáticamente y no se perderán al reiniciar")
            print("\n--- COMANDOS ÚTILES ---")
            print("• Ctrl+C: Detener servidor")
            print(f"• Agregar clanes: Ve a http://localhost:{PORT}/api/add-clan")
            print("\n🎯 ¡Listo! Tu sistema está funcionando")
            
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"❌ Error: El puerto {PORT} está ocupado")
            print("💡 Soluciones:")
            print("   1. Mata el proceso anterior: pkill -f python")
            print(f"   2. Cambia el puerto en la línea: PORT = {PORT}")
            print("   3. Reinicia Termux completamente")
        else:
            print(f"❌ Error iniciando servidor: {e}")
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido por el usuario")
        print("💾 Todos los datos han sido guardados correctamente")

if __name__ == "__main__":
    main()
rm clash_server.py
nano clash_server.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta
import schedule

# Configuración
PORT = 3001
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImQzYjBmYzMzLWU2NmQtNGQzNC1iY2QwLWIzOTI4NWNiYzgwOSIsImlhdCI6MTczMzc5NzA4NSwic3ViIjoiZGV2ZWxvcGVyL2YwNmEwZDczLWNmMTEtNGY4Yi1hNjNjLTk1MzZkOGEzNDFlMCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjc4LjEzOS4yNDAuMCIsIjc4LjEzOS4yNDAuMjU1Il0sInR5cGUiOiJjbGllbnQifV19.xgczE6lTTyUhIYa-EGjPvYKjCYIGzLtE2DRvXD9CQDmAMmslPLVfaevzEGJPOWkJFzC-jGVrlVxBJUMzx7qbEw"

# Archivos de datos
CLANS_FILE = "clans.json"
DONATIONS_FILE = "donations_data.json"

# Zona horaria Argentina
ARGENTINA_TZ = timezone(timedelta(hours=-3))

def load_clans():
    """Cargar clanes desde archivo"""
    if os.path.exists(CLANS_FILE):
        with open(CLANS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"#2LJULC0Q": "REQUEST & LEAVE"}

def save_clans(clans):
    """Guardar clanes"""
    with open(CLANS_FILE, 'w', encoding='utf-8') as f:
        json.dump(clans, f, indent=2, ensure_ascii=False)

def load_donations_data():
    """Cargar datos de donaciones"""
    if os.path.exists(DONATIONS_FILE):
        with open(DONATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_donations_data(data):
    """Guardar datos de donaciones"""
    with open(DONATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_clan_data(clan_tag):
    """Obtener datos del clan desde la API"""
    try:
        encoded_tag = urllib.parse.quote(clan_tag, safe='')
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {API_KEY}')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error obteniendo datos del clan {clan_tag}: {e}")
        return None

def process_donations():
    """Procesar donaciones (totales y diarias)"""
    donations_data = load_donations_data()
    clans = load_clans()
    current_time = datetime.now(ARGENTINA_TZ)
    
    for clan_tag in clans:
        clan_data = get_clan_data(clan_tag)
        if not clan_data:
            continue
            
        clan_key = clan_tag.replace('#', '')
        
        if clan_key not in donations_data:
            donations_data[clan_key] = {
                'clan_info': {},
                'players': {},
                'last_reset': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'last_update': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Actualizar info del clan
        donations_data[clan_key]['clan_info'] = {
            'name': clan_data.get('name', ''),
            'tag': clan_data.get('tag', ''),
            'description': clan_data.get('description', ''),
            'clanLevel': clan_data.get('clanLevel', 0),
            'clanPoints': clan_data.get('clanPoints', 0),
            'members': clan_data.get('members', 0),
            'warWins': clan_data.get('warWins', 0),
            'location': clan_data.get('location', {}).get('name', 'International')
        }
        
        # Procesar miembros
        for member in clan_data.get('memberList', []):
            player_tag = member['tag']
            current_donations = member.get('donations', 0)
            current_received = member.get('donationsReceived', 0)
            
            if player_tag not in donations_data[clan_key]['players']:
                # Nuevo jugador
                donations_data[clan_key]['players'][player_tag] = {
                    'name': member['name'],
                    'role': member['role'],
                    'expLevel': member['expLevel'],
                    'league': member.get('league', {}),
                    'trophies': member['trophies'],
                    'total_donations': current_donations,
                    'total_received': current_received,
                    'daily_donations': 0,
                    'daily_received': 0,
                    'last_donations': current_donations,
                    'last_received': current_received
                }
            else:
                # Jugador existente
                player_data = donations_data[clan_key]['players'][player_tag]
                
                # Calcular donaciones diarias
                daily_donated = current_donations - player_data.get('last_donations', 0)
                daily_received = current_received - player_data.get('last_received', 0)
                
                # Si las donaciones actuales son menores, significa que se reinició
                if current_donations < player_data.get('last_donations', 0):
                    daily_donated = current_donations
                if current_received < player_data.get('last_received', 0):
                    daily_received = current_received
                
                # Actualizar datos
                player_data.update({
                    'name': member['name'],
                    'role': member['role'],
                    'expLevel': member['expLevel'],
                    'league': member.get('league', {}),
                    'trophies': member['trophies'],
                    'total_donations': max(player_data.get('total_donations', 0), current_donations),
                    'total_received': max(player_data.get('total_received', 0), current_received),
                    'daily_donations': player_data.get('daily_donations', 0) + max(0, daily_donated),
                    'daily_received': player_data.get('daily_received', 0) + max(0, daily_received),
                    'last_donations': current_donations,
                    'last_received': current_received
                })
        
        donations_data[clan_key]['last_update'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    save_donations_data(donations_data)
    return donations_data

def daily_reset():
    """Reset diario a las 2 AM"""
    donations_data = load_donations_data()
    current_time = datetime.now(ARGENTINA_TZ)
    
    for clan_key in donations_data:
        for player_tag in donations_data[clan_key]['players']:
            donations_data[clan_key]['players'][player_tag]['daily_donations'] = 0
            donations_data[clan_key]['players'][player_tag]['daily_received'] = 0
        
        donations_data[clan_key]['last_reset'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    save_donations_data(donations_data)
    print(f"Reset diario completado a las {current_time.strftime('%H:%M:%S')}")

# HTML minificado para evitar problemas de sintaxis
HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top Req Clans</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
        .header { background: linear-gradient(90deg, #ff6b35, #f9ca24); color: white; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .section { background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        select { width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
        .table-header { display: grid; grid-template-columns: 50px 1fr 120px 120px; background: #34495e; color: white; padding: 15px 10px; font-weight: bold; }
        .player-row { display: grid; grid-template-columns: 50px 1fr 120px 120px; padding: 15px 10px; border-bottom: 1px solid #eee; }
        .player-row:nth-child(even) { background: #f8f9fa; }
    </style>
</head>
<body>
    <div class="header">🏆 TOP REQ CLANS</div>
    <div class="container">
        <div class="section">
            <h3>Seleccionar Clan:</h3>
            <select id="clanSelect" onchange="loadClanData()">
                <option value="">Cargando...</option>
            </select>
        </div>
        <div id="clanInfo" style="display: none;">
            <div class="section">
                <h2 id="clanName">Cargando...</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="memberCount">0</div>
                        <div class="stat-label">Members</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalDailyDonations">0</div>
                        <div class="stat-label">Daily Donations</div>
                    </div>
                </div>
            </div>
            <div class="section">
                <div class="table-header">
                    <div>Rank</div>
                    <div>Player</div>
                    <div>Donations</div>
                    <div>Received</div>
                </div>
                <div id="playersContainer">Loading...</div>
            </div>
        </div>
    </div>
    <script>
        let currentClan = '';
        let clanData = {};
        
        async function loadClans() {
            try {
                const response = await fetch('/api/clans');
                const clans = await response.json();
                const select = document.getElementById('clanSelect');
                select.innerHTML = '<option value="">Select clan</option>';
                for (const [tag, name] of Object.entries(clans)) {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = name + ' (' + tag + ')';
                    select.appendChild(option);
                }
                if (Object.keys(clans).length > 0) {
                    select.value = Object.keys(clans)[0];
                    loadClanData();
                }
            } catch (error) {
                console.error('Error loading clans:', error);
            }
        }
        
        async function loadClanData() {
            const select = document.getElementById('clanSelect');
            currentClan = select.value;
            if (!currentClan) {
                document.getElementById('clanInfo').style.display = 'none';
                return;
            }
            document.getElementById('clanInfo').style.display = 'block';
            try {
                const response = await fetch('/api/clan/' + encodeURIComponent(currentClan));
                clanData = await response.json();
                updateInterface();
            } catch (error) {
                console.error('Error loading clan data:', error);
            }
        }
        
        function updateInterface() {
            document.getElementById('clanName').textContent = clanData.clan_info.name;
            document.getElementById('memberCount').textContent = clanData.clan_info.members || '0';
            
            let totalDaily = 0;
            const players = Object.values(clanData.players);
            players.forEach(player => totalDaily += player.daily_donations || 0);
            document.getElementById('totalDailyDonations').textContent = totalDaily.toLocaleString();
            
            players.sort((a, b) => (b.daily_donations || 0) - (a.daily_donations || 0));
            
            let html = '';
            players.forEach((player, index) => {
                html += '<div class="player-row">';
                html += '<div>' + (index + 1) + '</div>';
                html += '<div>' + player.name + '</div>';
                html += '<div>' + (player.daily_donations || 0).toLocaleString() + '</div>';
                html += '<div>' + (player.daily_received || 0).toLocaleString() + '</div>';
                html += '</div>';
            });
            
            document.getElementById('playersContainer').innerHTML = html;
        }
        
        window.onload = function() {
            loadClans();
            setInterval(() => { if (currentClan) loadClanData(); }, 5 * 60 * 1000);
        };
    </script>
</body>
</html>"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
            
        elif self.path == "/api/clans":
            clans = load_clans()
            self.send_json_response(clans)
            
        elif self.path.startswith("/api/clan/"):
            clan_tag = urllib.parse.unquote(self.path.split("/")[-1])
            donations_data = process_donations()
            
            clan_key = clan_tag.replace('#', '')
            if clan_key in donations_data:
                self.send_json_response(donations_data[clan_key])
            else:
                self.send_json_response({"error": "Clan no encontrado"})
                
        elif self.path == "/api/add-clan":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            add_clan_html = """<html><body>
            <h2>Agregar Clan</h2>
            <form method="POST" action="/api/add-clan">
                <p>Tag: <input type="text" name="clan_tag" placeholder="#2LJULC0Q" required></p>
                <p>Name: <input type="text" name="clan_name" placeholder="Mi Clan" required></p>
                <p><button type="submit">Agregar</button></p>
            </form>
            <p><a href="/">Volver</a></p>
            </body></html>"""
            self.wfile.write(add_clan_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/api/add-clan":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            clan_tag = params.get('clan_tag', [''])[0].strip()
            clan_name = params.get('clan_name', [''])[0].strip()
            
            if clan_tag and clan_name:
                if not clan_tag.startswith('#'):
                    clan_tag = '#' + clan_tag
                    
                clans = load_clans()
                clans[clan_tag] = clan_name
                save_clans(clans)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                success_html = f"""<html><body>
                <h2>Clan agregado!</h2>
                <p>{clan_name} ({clan_tag})</p>
                <p><a href="/">Dashboard</a></p>
                </body></html>"""
                self.wfile.write(success_html.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        return

def run_scheduler():
    """Ejecutar programador en hilo separado"""
    schedule.every().day.at("02:00").do(daily_reset)
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    print("🚀 Iniciando servidor...")
    print(f"🌐 URL: http://localhost:{PORT}")
    
    # Crear archivos si no existen
    if not os.path.exists(CLANS_FILE):
        save_clans({"#2LJULC0Q": "REQUEST & LEAVE"})
    if not os.path.exists(DONATIONS_FILE):
        save_donations_data({})
    
    # Procesar datos inicial
    process_donations()
    
    # Iniciar scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Iniciar servidor
    try:
        with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
            print(f"✅ Servidor en http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"❌ Puerto {PORT} ocupado. Usa: pkill -f python")
        else:
            print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")

if __name__ == "__main__":
    main()
