import requests
import json
import time
from datetime import datetime
import os

# Configuración
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjFkYzk0MjBmLTMxN2UtNGIwYy05OGYyLTgxMmRmYmNmYTRjYSIsImlhdCI6MTc1MTUwODg2NCwic3ViIjoiZGV2ZWxvcGVyL2ZjNTE2YWY0LTA4YzUtY TUwYS1iNjA1LTA0NWJiN2Y2MWYxNyIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt 7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZH JzIjpbIjIwMS4xNzguMjU0Ljk5Il0sInR5cGUiOiJjbGllbnQifV19.keOTGZJMyEoTf8- dGKb9uTMnjh4xPvj9OnTjLTMrjgm4Z2jDa8nFYDGtoFF_qwO9Iy8YU48YZpDvlD1LRJKa3g"
CLAN_TAG = "22G8YL992"

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
            print(f"❌ Error en la API: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return None

def generate_html(clan_data):
    """Genera el HTML con los datos de donaciones"""
    if not clan_data:
        return """
        <html>
        <head><title>Error</title></head>
        <body>
        <h1>Error al cargar datos del clan</h1>
        <p>Verifica tu conexión a internet y la API key</p>
        </body>
        </html>
        """
    
    # Ordenar miembros por donaciones
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
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                margin: 0;
                padding: 10px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }}
            h1 {{
                text-align: center;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }}
            .stats {{
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            .stat-box {{
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin: 5px;
                min-width: 120px;
            }}
            .stat-number {{
                font-size: 1.8em;
                font-weight: bold;
                color: #ffdd59;
            }}
            .members-list {{
                margin-top: 20px;
            }}
            .member {{
                background: rgba(255, 255, 255, 0.1);
                margin: 5px 0;
                padding: 10px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .member:nth-child(odd) {{
                background: rgba(255, 255, 255, 0.05);
            }}
            .member-name {{
                font-weight: bold;
            }}
            .member-donations {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .update-time {{
                text-align: center;
                margin-top: 20px;
                font-style: italic;
                opacity: 0.8;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 {clan_data.get('name', 'Clan')} 🏆</h1>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{total_donations:,}</div>
                    <div>Total Donado</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_received:,}</div>
                    <div>Total Recibido</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{len(members)}</div>
                    <div>Miembros</div>
                </div>
            </div>
            
            <div class="members-list">
                <h2>🎖️ Ranking de Donadores</h2>
    """
    
    for i, member in enumerate(members[:20], 1):  # Solo top 20
        name = member.get('name', 'Sin nombre')
        donations = member.get('donations', 0)
        received = member.get('donationsReceived', 0)
        
        html += f"""
                <div class="member">
                    <span>#{i} {name}</span>
                    <span class="member-donations">💎{donations:,} | 📥{received:,}</span>
                </div>
        """
    
    html += f"""
            </div>
            
            <div class="update-time">
                ⏰ Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                <br>🔄 Se actualiza cada 3 minutos automáticamente
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def main():
    print("🚀 Iniciando Simple Clash Tracker...")
    print(f"📊 Clan: #{CLAN_TAG}")
    print("-" * 40)
    
    while True:
        print(f"🔄 Actualizando... {datetime.now().strftime('%H:%M:%S')}")
        
        # Obtener datos del clan
        clan_data = get_clan_data()
        
        if clan_data:
            # Generar HTML
            html_content = generate_html(clan_data)
            
            # Guardar archivo
            with open('donations.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("✅ Archivo donations.html actualizado")
            print("🌐 Abre donations.html en tu navegador para verlo")
            print(f"📈 Total donaciones: {sum(m.get('donations', 0) for m in clan_data.get('memberList', []))}")
        else:
            print("❌ No se pudieron obtener los datos")
        
        print(f"⏱️ Próxima actualización en 3 minutos...")
        print("-" * 40)
        
        # Esperar 3 minutos
        time.sleep(180)

if __name__ == "__main__":
    main()
