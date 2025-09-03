import requests
import json
import time
from datetime import datetime
import os

# Configuración
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjQ0MmM5NDI3LWRmZWUtNDUzOS05YzM3LTY0YTI4ZWQ3NWQ2YSIsImlhdCI6MTc1NDc4NzA4NCwic3ViIjoiZGV2ZWxvcGVyL2ZjNTE2YWY0LTA4YzUtYTUwYS1iNjA1LTA0NWJiN2Y2MWYxNyIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjE5MC40OC4xMTkuMTAwIl0sInR5cGUiOiJjbGllbnQifV19.wX0TqtjSP7HUxVs9cvopoFZk_5wp-fG70HOrQaF-EOBKgUUBYXySAU7GMfnOx8ivnqB3qgKv-Urb_S79dBEpQw"

CLAN_TAG = "22G8YL992"

print("🚀 Iniciando Clash of Clans Donations Tracker...")
print(f"🔍 Consultando API para clan #{CLAN_TAG}...")

def obtener_datos_clan():
    url = f"https://api.clashofclans.com/v1/clans/%23{CLAN_TAG}"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def generar_html(datos_clan):
    if not datos_clan:
        return
    
    # Procesar miembros
    miembros = datos_clan['memberList']
    miembros.sort(key=lambda x: x['donations'], reverse=True)
    
    # Generar HTML
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{datos_clan['name']} - Donations Tracker</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            padding: 30px;
            text-align: center;
            color: white;
        }}
        .clan-name {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .stat {{
            background: rgba(255,255,255,0.2);
            padding: 15px 25px;
            border-radius: 10px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            display: block;
        }}
        .members {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .member {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #FF6B6B;
            position: relative;
            transition: transform 0.3s ease;
        }}
        .member:hover {{
            transform: translateY(-5px);
        }}
        .rank {{
            position: absolute;
            top: -10px;
            right: 15px;
            background: #FF6B6B;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}
        .member-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .role {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .role.leader {{ background: #FFD700; color: #333; }}
        .role.coleader {{ background: #FF6B6B; color: white; }}
        .role.elder {{ background: #4ECDC4; color: white; }}
        .role.member {{ background: #95a5a6; color: white; }}
        .donations-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        .donation-stat {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .donation-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #FF6B6B;
        }}
        .donation-label {{
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
        }}
        .auto-refresh {{ color: #4ECDC4; font-weight: bold; }}
        @media (max-width: 768px) {{
            .stats {{ flex-direction: column; align-items: center; }}
            .members {{ grid-template-columns: 1fr; padding: 15px; }}
            .clan-name {{ font-size: 2em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="clan-name">🏆 {datos_clan['name']}</h1>
            <div class="stats">
                <div class="stat">
                    <span class="stat-value">{sum(m['donations'] for m in miembros):,}</span>
                    <span class="stat-label">Donaciones Totales</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{len(miembros)}</span>
                    <span class="stat-label">Miembros</span>
                </div>
                <div class="stat">
                    <span class="stat-value">Nivel {datos_clan['clanLevel']}</span>
                    <span class="stat-label">Clan</span>
                </div>
            </div>
        </div>
        
        <div class="members">
"""
    
    # Agregar miembros
    for i, miembro in enumerate(miembros):
        role_class = miembro['role'].lower().replace(' ', '')
        html += f"""
            <div class="member">
                <div class="rank">{i+1}</div>
                <div class="member-name">{miembro['name']}</div>
                <div class="role {role_class}">{miembro['role']}</div>
                <div class="donations-grid">
                    <div class="donation-stat">
                        <div class="donation-value">{miembro['donations']:,}</div>
                        <div class="donation-label">Donaciones</div>
                    </div>
                    <div class="donation-stat">
                        <div class="donation-value">{miembro['donationsReceived']:,}</div>
                        <div class="donation-label">Recibidas</div>
                    </div>
                </div>
            </div>
        """
    
    html += f"""
        </div>
        
        <div class="footer">
            Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
            <span class="auto-refresh">🔄 Se actualiza automáticamente cada 3 minutos</span>
        </div>
    </div>
    
    <script>
        // Auto-refresh cada 3 minutos
        setTimeout(() => location.reload(), 180000);
        
        // Contador en el título
        let seconds = 180;
        function updateTitle() {{
            if (seconds <= 0) return;
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            document.title = `(${{minutes}}:${{secs.toString().padStart(2, '0')}}) {datos_clan['name']} - Donations`;
            seconds--;
            setTimeout(updateTitle, 1000);
        }}
        updateTitle();
    </script>
</body>
</html>
"""
    
    # Guardar archivo
    with open('clan_donations.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Archivo HTML generado correctamente!")
    print("📄 Abrí el archivo 'clan_donations.html' en tu navegador")

def main():
    while True:
        datos = obtener_datos_clan()
        if datos:
            generar_html(datos)
            print(f"⏰ Próxima actualización en 3 minutos...")
        else:
            print("❌ No se pudieron obtener los datos. Reintentando en 3 minutos...")
        
        time.sleep(180)  # 3 minutos

if __name__ == "__main__":
    main()
