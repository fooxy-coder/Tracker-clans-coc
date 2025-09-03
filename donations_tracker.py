import requests
import json
import time
from datetime import datetime
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

# Configuración
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImU5ZGM2NTZhLTk0MTUTNDAwNy1hYWJmLTAwOTExZDE1NDliYiIsImlhdCI6MTc1MTUxNDU2Nywic3ViIjoiZGV2ZWxvcGVyL2ZjNTE2YWY0LTA4YzUtY TUwYS1iNjA1LTA0NWJiN2Y2MWYxNyIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt 7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZH JzIjpbIjIwMS4xNzguMjU0Ljk5Il0sInR5cGUiOiJjbGllbnQifV19.fhbe7BGl4IxxMU8 AT5R7Qk3LhI_L9aigBXSTRbXU7iZoiFLz3bxU_Ypdy6LGy0Y0KYgOno_ETJxlLTglYfL-_w"
CLAN_TAG = "22G8YL992"
UPDATE_INTERVAL = 180  # 3 minutos en segundos

# Headers para la API
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Accept': 'application/json'
}

def get_clan_data():
    """Obtiene datos del clan desde la API"""
    try:
        url = f"https://api.clashofclans.com/v1/clans/%23{CLAN_TAG}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en la API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return None

def generate_html(clan_data):
    """Genera el HTML con los datos de donaciones"""
    if not clan_data:
        return "<html><body><h1>Error al cargar datos del clan</h1></body></html>"
    
    # Ordenar miembros por donaciones (mayor a menor)
    members = sorted(clan_data.get('memberList', []), 
                    key=lambda x: x.get('donations', 0), reverse=True)
    
    total_donations = sum(member.get('donations', 0) for member in members)
    total_received = sum(member.get('donationsReceived', 0) for member in members)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Donaciones - {clan_data.get('name', 'Clan')}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="180">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                backdrop-filter: blur(10px);
            }}
            h1 {{
                text-align: center;
                color: #fff;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                margin-bottom: 10px;
            }}
            .stats {{
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            .stat-box {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                min-width: 150px;
                margin: 10px;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #ffdd59;
            }}
            .members-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                overflow: hidden;
            }}
            .members-table th {{
                background: rgba(0, 0, 0, 0.3);
                padding: 15px;
                text-align: left;
                font-weight: bold;
            }}
            .members-table td {{
                padding: 12px 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .members-table tr:nth-child(even) {{
                background: rgba(255, 255, 255, 0.05);
            }}
            .members-table tr:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            .role {{
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
            }}
            .leader {{ background: #ff6b6b; }}
            .coLeader {{ background: #ff9f43; }}
            .elder {{ background: #feca57; color: #333; }}
            .member {{ background: #48dbfb; color: #333; }}
            .last-updated {{
                text-align: center;
                margin-top: 20px;
                font-style: italic;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 {clan_data.get('name', 'Clan')} 🏆</h1>
            <p style="text-align: center; opacity: 0.9;">#{CLAN_TAG} • {len(members)} miembros</p>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{total_donations:,}</div>
                    <div>Donaciones Totales</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_received:,}</div>
                    <div>Recibidas Totales</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{clan_data.get('clanLevel', 'N/A')}</div>
                    <div>Nivel del Clan</div>
                </div>
            </div>
            
            <table class="members-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Jugador</th>
                        <th>Rol</th>
                        <th>Donaciones</th>
                        <th>Recibidas</th>
                        <th>Ratio</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, member in enumerate(members, 1):
        name = member.get('name', 'Sin nombre')
        role = member.get('role', 'member')
        donations = member.get('donations', 0)
        received = member.get('donationsReceived', 0)
        ratio = f"{donations/max(received, 1):.1f}" if received > 0 else "∞" if donations > 0 else "0"
        
        role_class = role.lower().replace(' ', '')
        role_display = {
            'leader': 'Líder',
            'coleader': 'Co-líder', 
            'elder': 'Veterano',
            'member': 'Miembro'
        }.get(role_class, role)
        
        html += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{name}</td>
                        <td><span class="role {role_class}">{role_display}</span></td>
                        <td>{donations:,}</td>
                        <td>{received:,}</td>
                        <td>{ratio}</td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>
            
            <div class="last-updated">
                Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                <br>Se actualiza automáticamente cada 3 minutos
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def update_html():
    """Actualiza el archivo HTML cada 3 minutos"""
    while True:
        print(f"Actualizando datos... {datetime.now().strftime('%H:%M:%S')}")
        clan_data = get_clan_data()
        
        if clan_data:
            html_content = generate_html(clan_data)
            
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("✅ Datos actualizados correctamente")
        else:
            print("❌ Error al obtener datos del clan")
        
        time.sleep(UPDATE_INTERVAL)

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciar logs del servidor web
        pass

def start_server():
    """Inicia el servidor web"""
    try:
        server = HTTPServer(('0.0.0.0', 8080), CustomHTTPRequestHandler)
        print("🌐 Servidor iniciado en: http://localhost:8080")
        print("📱 Para acceder desde otros dispositivos usa tu IP local")
        server.serve_forever()
    except Exception as e:
        print(f"Error al iniciar servidor: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Clash of Clans Donations Tracker...")
    print(f"📊 Clan: #{CLAN_TAG}")
    print(f"⏰ Actualización cada {UPDATE_INTERVAL//60} minutos")
    print("-" * 50)
    
    # Crear el primer archivo HTML
    print("Generando página inicial...")
    clan_data = get_clan_data()
    if clan_data:
        html_content = generate_html(clan_data)
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("✅ Página inicial creada")
    
    # Iniciar el hilo de actualización
    update_thread = threading.Thread(target=update_html, daemon=True)
    update_thread.start()
    
    # Iniciar servidor web
    start_server()
