#!/usr/bin/env python3

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import socket
from datetime import datetime, timezone, timedelta
import threading
import time

# Configuración del puerto
PORT = 8000

# Configuración API Clash of Clans
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImNhMzdhYTY4LWJhNmUtNDEzNi1iNDg1LTM2Yzk2MDA2N2NhNSIsImlhdCI6MTc1NjY5MTE4NCwic3ViIjoiZGV2ZWxvcGVyL2ZjNTE2YWY0LTA4YzUtY TUwYS1iNjA1LTA0NWJiN2Y2MWYxNyIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjIwMS4xNzguMjQ3Ljg1Il0sInR5cGUiOiJjbGllbnQifV19.W6s64MnPDBt2CtZqCsAkpYTpMYu_985EkTa_og2F1C5KdSPWS1NgBbTjkD-ujT4ssG6U0w6RicROb-Nhkgd5Sg"
API_BASE_URL = "https://api.clashofclans.com/v1"

# Cache para datos de clanes
clan_cache = {}
daily_stats_cache = {}
last_update = None

# Variables para controlar el reset diario
last_reset_date = None
reset_in_progress = False
reset_lock = threading.Lock()

# Archivos para persistir datos
DONATIONS_FILE = "daily_donations.json"
BACKUP_FILE = "donations_backup.json"

def save_daily_donations():
    """Guarda las donaciones diarias en archivo con respaldo automatico"""
    try:
        # Crear respaldo del archivo anterior
        if os.path.exists(DONATIONS_FILE):
            import shutil
            shutil.copy2(DONATIONS_FILE, BACKUP_FILE)
        
        # Agregar timestamp al archivo
        data_to_save = {
            'last_save': datetime.now().isoformat(),
            'version': '2.1_fixed_reset',
            'last_reset_date': last_reset_date.isoformat() if last_reset_date else None,
            'stats': daily_stats_cache
        }
        
        with open(DONATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Estadísticas guardadas exitosamente - {len(daily_stats_cache)} registros")
        return True
    except Exception as e:
        print(f"❌ Error guardando donaciones: {e}")
        return False

def load_daily_donations():
    """Carga las donaciones diarias desde archivo con sistema de recuperacion"""
    global daily_stats_cache, last_reset_date
    
    def try_load_file(filepath):
        """Intenta cargar un archivo especifico"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Si es el nuevo formato con metadata
                if isinstance(data, dict) and 'stats' in data:
                    # Cargar fecha del ultimo reset si existe
                    if 'last_reset_date' in data and data['last_reset_date']:
                        try:
                            last_reset_date = datetime.fromisoformat(data['last_reset_date'].replace('Z', '+00:00'))
                        except:
                            last_reset_date = None
                    
                    return data['stats']
                # Si es el formato anterior (directamente el diccionario)
                else:
                    return data
        except Exception as e:
            print(f"⚠️ Error leyendo {filepath}: {e}")
            return None

    # Intentar cargar archivo principal
    loaded_data = try_load_file(DONATIONS_FILE)
    
    # Si falla, intentar cargar respaldo
    if loaded_data is None:
        print("🔍 Archivo principal fallo, intentando respaldo...")
        loaded_data = try_load_file(BACKUP_FILE)
    
    if loaded_data is not None:
        daily_stats_cache = loaded_data
        print(f"📊 Estadísticas cargadas exitosamente")
        print(f"🔢 {len([k for k in daily_stats_cache.keys() if not k.endswith('_reset')])} jugadores en cache")
        
        if last_reset_date:
            print(f"🕐 Último reset: {last_reset_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Intentar recuperar estadisticas del dia
        recover_daily_stats()
    else:
        print("🆕 No hay archivos de estadísticas - empezando limpio")
        daily_stats_cache = {}
        last_reset_date = None
        # Hacer un backup inicial vacio
        save_daily_donations()

def force_daily_reset():
    """Fuerza un reset manual de las donaciones diarias"""
    global daily_stats_cache, last_reset_date, reset_in_progress
    
    with reset_lock:
        if reset_in_progress:
            print("⏸️ Reset ya en progreso, cancelando...")
            return False
        
        reset_in_progress = True
    
    try:
        print("🔄 FORZANDO RESET MANUAL DE DONACIONES DIARIAS...")
        
        # Obtener datos actuales de todos los clanes
        clans = load_clans()
        reset_count = 0
        
        for clan_tag in clans.keys():
            try:
                clan_data = get_clan_data_from_api(clan_tag)
                if not clan_data or not clan_data.get('memberList'):
                    continue
                    
                for member in clan_data['memberList']:
                    member_tag = member.get('tag', '')
                    cache_key = f"{clan_tag}_{member_tag}"
                    current_donations = member.get('donations', 0)
                    current_received = member.get('donationsReceived', 0)
                    
                    # Resetear completamente las estadisticas diarias
                    daily_stats_cache[cache_key] = {
                        'last_total_donations': current_donations,
                        'last_total_received': current_received,
                        'daily_donations': 0,
                        'daily_received': 0,
                        'last_update': datetime.now().isoformat(),
                        'manual_reset': True,
                        'reset_timestamp': datetime.now().isoformat()
                    }
                    
                    reset_count += 1
                    member_name = member.get('name', 'Unknown')[:15]
                    print(f"🔄 Reset {member_name}: base_don={current_donations}, base_rec={current_received}")
            
            except Exception as e:
                print(f"❌ Error en reset para clan {clan_tag}: {e}")
        
        # Actualizar fecha del ultimo reset
        last_reset_date = datetime.now()
        
        # Guardar inmediatamente despues del reset
        if save_daily_donations():
            print(f"✅ Reset manual completado - {reset_count} jugadores reseteados")
            print("💡 Haz algunas donaciones en el juego para ver los cambios")
            return True
        else:
            print("❌ Error guardando reset")
            return False
    
    finally:
        reset_in_progress = False

def recover_daily_stats():
    """Intenta recuperar las donaciones y tropas recibidas de hoy"""
    global daily_stats_cache
    
    print("📊 Intentando recuperar estadísticas del día actual...")
    
    # Obtener hora argentina actual
    argentina_tz = timezone(timedelta(hours=-3))
    now_argentina = datetime.now(argentina_tz)
    
    # Solo intentar recovery despues de las 6 AM para evitar conflictos con reset
    if now_argentina.hour < 6:
        print("🕕 Es muy temprano, esperando hasta las 6 AM para recovery")
        return
    
    clans = load_clans()
    recovered_count = 0
    
    for clan_tag in clans.keys():
        try:
            clan_data = get_clan_data_from_api(clan_tag)
            if not clan_data or not clan_data.get('memberList'):
                continue
                
            for member in clan_data['memberList']:
                member_tag = member.get('tag', '')
                cache_key = f"{clan_tag}_{member_tag}"
                
                if cache_key not in daily_stats_cache:
                    # Si no existe, crear entrada nueva
                    daily_stats_cache[cache_key] = {
                        'last_total_donations': member.get('donations', 0),
                        'last_total_received': member.get('donationsReceived', 0),
                        'daily_donations': 0,
                        'daily_received': 0,
                        'last_update': now_argentina.isoformat(),
                        'new_player': True
                    }
                    print(f"🆕 Nuevo jugador: {member.get('name', 'Unknown')[:15]}")
                    continue
                
                cache_data = daily_stats_cache[cache_key]
                current_donations = member.get('donations', 0)
                current_received = member.get('donationsReceived', 0)
                last_total_donations = cache_data.get('last_total_donations', current_donations)
                last_total_received = cache_data.get('last_total_received', current_received)
                
                # Si hay poca actividad diaria registrada pero los totales sugieren actividad
                current_daily = cache_data.get('daily_donations', 0)
                if (current_daily < 5 and current_donations > last_total_donations):
                    
                    estimated_daily_donations = current_donations - last_total_donations
                    estimated_daily_received = max(0, current_received - last_total_received)
                    
                    # Solo recuperar si la diferencia es razonable (menos de 1000 por dia)
                    if estimated_daily_donations < 1000:
                        # Actualizar cache con estimacion
                        daily_stats_cache[cache_key].update({
                            'daily_donations': estimated_daily_donations,
                            'daily_received': estimated_daily_received,
                            'last_total_donations': current_donations,
                            'last_total_received': current_received,
                            'recovered': True,
                            'recovery_timestamp': now_argentina.isoformat()
                        })
                        
                        recovered_count += 1
                        member_name = member.get('name', 'Unknown')[:15]
                        print(f"🔧 Recuperado {member_name}: {estimated_daily_donations}don, {estimated_daily_received}rec")
        
        except Exception as e:
            print(f"❌ Error en recovery para clan {clan_tag}: {e}")
    
    if recovered_count > 0:
        save_daily_donations()
        print(f"✅ Recovery completado: {recovered_count} jugadores actualizados")
    else:
        print("ℹ️ No se necesito recovery")

def load_clans():
    """Devuelve la lista de clanes a monitorear"""
    return {
        "22G8YL992": "req n go",
        "9PCULGVU": "Mi Nuevo Clan"
    }

def make_api_request(endpoint):
    """Realiza una peticion a la API de Clash of Clans"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Accept': 'application/json',
            'User-Agent': 'ClashTracker/2.0',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        print(f"🔗 API: {endpoint}")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ API OK: {endpoint}")
                return data
            else:
                print(f"❌ API Error: Status {response.status}")
                return None
    except urllib.error.HTTPError as e:
        error_msg = ""
        try:
            error_response = e.read().decode('utf-8')
            error_detail = json.loads(error_response)
            error_msg = error_detail.get('message', 'Unknown error')
        except:
            error_msg = e.reason
        print(f"❌ HTTP Error {e.code}: {error_msg}")
        if e.code == 403:
            print("🔑 Error 403: Verifica tu API Key y que tu IP este autorizada")
        elif e.code == 404:
            print(f"🔍 Error 404: Clan no encontrado")
        elif e.code == 429:
            print("⏰ Error 429: Limite de peticiones excedido")
        return None
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return None

def check_daily_reset():
    """Verifica si es hora de resetear estadisticas diarias"""
    global daily_stats_cache, last_reset_date, reset_in_progress
    
    # Thread safety - Solo un hilo puede hacer reset a la vez
    with reset_lock:
        if reset_in_progress:
            return False
        
        # Obtener tiempo actual en Argentina (UTC-3)
        argentina_tz = timezone(timedelta(hours=-3))
        now_argentina = datetime.now(argentina_tz)
        today_date = now_argentina.date()
        
        # Solo resetear una vez por dia
        if last_reset_date and last_reset_date.date() >= today_date:
            return False
        
        # Ventana de tiempo - Entre 2:00 y 2:30 AM
        if not (2 <= now_argentina.hour <= 2 and now_argentina.minute <= 30):
            return False
        
        # Marcar reset en progreso
        reset_in_progress = True
    
    try:
        print(f"🌙 ¡RESET AUTOMATICO A LAS 2 AM ARGENTINA! - {now_argentina.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Obtener datos actuales antes del reset
        clans = load_clans()
        reset_count = 0
        
        # Resetear todas las estadisticas diarias manteniendo el ultimo total conocido
        for clan_tag in clans.keys():
            try:
                clan_data = get_clan_data_from_api(clan_tag)
                if not clan_data or not clan_data.get('memberList'):
                    continue
                
                for member in clan_data['memberList']:
                    member_tag = member.get('tag', '')
                    cache_key = f"{clan_tag}_{member_tag}"
                    current_donations = member.get('donations', 0)
                    current_received = member.get('donationsReceived', 0)
                    
                    if cache_key in daily_stats_cache:
                        # Actualizar con datos actuales y resetear diarios
                        daily_stats_cache[cache_key].update({
                            'last_total_donations': current_donations,
                            'last_total_received': current_received,
                            'daily_donations': 0,
                            'daily_received': 0,
                            'last_update': now_argentina.isoformat(),
                            'auto_reset': True,
                            'reset_time': now_argentina.isoformat()
                        })
                    else:
                        # Crear nueva entrada para jugadores nuevos
                        daily_stats_cache[cache_key] = {
                            'last_total_donations': current_donations,
                            'last_total_received': current_received,
                            'daily_donations': 0,
                            'daily_received': 0,
                            'last_update': now_argentina.isoformat(),
                            'auto_reset': True,
                            'reset_time': now_argentina.isoformat()
                        }
                    
                    reset_count += 1
                    member_name = member.get('name', 'Unknown')[:15]
                    print(f"🔄 Reset automatico {member_name}: base={current_donations}")
            
            except Exception as e:
                print(f"❌ Error en reset automatico para clan {clan_tag}: {e}")
        
        # Actualizar fecha del ultimo reset
        last_reset_date = now_argentina
        
        # Guardar inmediatamente
        if save_daily_donations():
            print(f"✅ Reset automatico completado - {reset_count} jugadores reseteados")
            return True
        else:
            print("❌ Error guardando reset automatico")
            return False
    
    except Exception as e:
        print(f"❌ Error en check_daily_reset: {e}")
        return False
    
    finally:
        # Siempre liberar el flag de reset
        reset_in_progress = False

def calculate_daily_stats(clan_tag, member_tag, current_donations, current_received):
    """Calcula donaciones Y tropas recibidas diarias"""
    global daily_stats_cache
    
    # Obtener hora argentina actual
    argentina_tz = timezone(timedelta(hours=-3))
    now_argentina = datetime.now(argentina_tz)
    
    # Clave para este miembro
    cache_key = f"{clan_tag}_{member_tag}"
    
    # Si no existe el registro, crearlo
    if cache_key not in daily_stats_cache:
        daily_stats_cache[cache_key] = {
            'last_total_donations': current_donations,
            'last_total_received': current_received,
            'daily_donations': 0,
            'daily_received': 0,
            'last_update': now_argentina.isoformat(),
            'created': now_argentina.isoformat()
        }
        # Guardar inmediatamente cuando se crea un nuevo jugador
        save_daily_donations()
        return 0, 0

    # Obtener datos anteriores
    cache_data = daily_stats_cache[cache_key]
    last_total_donations = cache_data.get('last_total_donations', current_donations)
    last_total_received = cache_data.get('last_total_received', current_received)
    daily_donations = cache_data.get('daily_donations', 0)
    daily_received = cache_data.get('daily_received', 0)

    # Detectar reset del juego (cuando los totales bajan significativamente)
    if current_donations < last_total_donations - 50:
        print(f"🔄 Reset del juego detectado para {member_tag}")
        daily_stats_cache[cache_key].update({
            'last_total_donations': current_donations,
            'last_total_received': current_received,
            'daily_donations': 0,
            'daily_received': 0,
            'last_update': now_argentina.isoformat(),
            'game_reset': True
        })
        save_daily_donations()
        return 0, 0

    # Calcular diferencias
    donations_diff = max(0, current_donations - last_total_donations)
    received_diff = max(0, current_received - last_total_received)

    # Solo actualizar si hay cambios
    if donations_diff > 0 or received_diff > 0:
        daily_donations += donations_diff
        daily_received += received_diff
        
        if donations_diff > 0:
            print(f"💰 {member_tag[-8:]}: +{donations_diff} donaciones (Total día: {daily_donations})")
        if received_diff > 0:
            print(f"🏆 {member_tag[-8:]}: +{received_diff} recibidas (Total día: {daily_received})")

        # Actualizar cache
        daily_stats_cache[cache_key].update({
            'last_total_donations': current_donations,
            'last_total_received': current_received,
            'daily_donations': daily_donations,
            'daily_received': daily_received,
            'last_update': now_argentina.isoformat()
        })

        # Guardar inmediatamente para no perder datos
        save_daily_donations()

    return daily_donations, daily_received

def get_clan_daily_summary(clan_tag):
    """Calcula el resumen de donaciones diarias del clan"""
    try:
        clan_data = get_clan_data_from_api(clan_tag)
        if not clan_data or not clan_data.get('memberList'):
            return {'total_daily_donations': 0, 'total_daily_received': 0, 'time_until_reset': ''}
        
        total_daily_donations = 0
        total_daily_received = 0
        
        for member in clan_data['memberList']:
            daily_donations = member.get('dailyDonations', 0)
            daily_received = member.get('dailyReceived', 0)
            total_daily_donations += daily_donations
            total_daily_received += daily_received
        
        # Calcular tiempo hasta el reset (2 AM Argentina)
        argentina_tz = timezone(timedelta(hours=-3))
        now_argentina = datetime.now(argentina_tz)
        
        # Si es despues de las 2 AM, el proximo reset es mañana a las 2 AM
        if now_argentina.hour >= 2:
            next_reset = now_argentina.replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            # Si es antes de las 2 AM, el reset es hoy a las 2 AM
            next_reset = now_argentina.replace(hour=2, minute=0, second=0, microsecond=0)
        
        time_diff = next_reset - now_argentina
        hours = int(time_diff.seconds // 3600)
        minutes = int((time_diff.seconds % 3600) // 60)
        seconds = int(time_diff.seconds % 60)
        
        time_until_reset = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return {
            'total_daily_donations': total_daily_donations,
            'total_daily_received': total_daily_received,
            'time_until_reset': time_until_reset
        }
        
    except Exception as e:
        print(f"❌ Error calculando resumen diario para clan {clan_tag}: {e}")
        return {'total_daily_donations': 0, 'total_daily_received': 0, 'time_until_reset': ''}

def get_clan_data_from_api(clan_tag):
    """Obtiene datos reales del clan desde la API de Clash of Clans"""
    global clan_cache

    # Limpiar el tag (remover # si esta presente)
    clean_tag = clan_tag.replace('#', '')
    print(f"🔍 Obteniendo datos del clan #{clean_tag}...")

    try:
        # Obtener informacion basica del clan
        clan_info = make_api_request(f"clans/%23{clean_tag}")
        if not clan_info:
            print(f"❌ No se pudo obtener info del clan #{clean_tag}")
            return get_fallback_clan_data(clan_tag)

        # Obtener miembros del clan
        members_info = clan_info.get('memberList', [])

        # Calcular totales
        total_donations = sum(member.get('donations', 0) for member in members_info)
        total_received = sum(member.get('donationsReceived', 0) for member in members_info)

        # Procesar lista de miembros con estadisticas diarias reales
        member_list = []
        for member in members_info:
            member_tag = member.get('tag', '')
            member_name = member.get('name', 'Unknown')
            current_donations = member.get('donations', 0)
            current_received = member.get('donationsReceived', 0)

            # Calcular estadisticas diarias reales
            daily_donations, daily_received = calculate_daily_stats(
                clean_tag, member_tag, current_donations, current_received
            )

            member_list.append({
                "tag": member_tag,
                "name": member_name,
                "donations": current_donations,
                "donationsReceived": current_received,
                "trophies": member.get('trophies', 0),
                "dailyDonations": daily_donations,
                "dailyReceived": daily_received
            })

        # Buscar lider
        leader_name = "Unknown"
        for member in members_info:
            if member.get('role') == 'leader':
                leader_name = member.get('name', 'Unknown')
                break

        clan_data = {
            "name": clan_info.get('name', 'Unknown Clan'),
            "members": clan_info.get('members', 0),
            "leader": leader_name,
            "totalDonations": total_donations,
            "totalReceived": total_received,
            "memberList": member_list,
            "level": clan_info.get('clanLevel', 1),
            "points": clan_info.get('clanPoints', 0)
        }

        # Actualizar cache
        clan_cache[clan_tag] = {
            "data": clan_data,
            "timestamp": datetime.now()
        }

        print(f"✅ Datos obtenidos para {clan_data['name']}: {total_donations:,} donaciones")
        return clan_data

    except Exception as e:
        print(f"❌ Error al obtener datos del clan #{clean_tag}: {str(e)}")
        return get_fallback_clan_data(clan_tag)

def get_fallback_clan_data(clan_tag):
    """Datos de respaldo si la API falla"""
    print(f"⚠️ Usando datos de respaldo para clan #{clan_tag}")
    clans = load_clans()
    clan_name = clans.get(clan_tag, f"Clan #{clan_tag}")

    return {
        "name": clan_name,  
        "members": 1,
        "leader": "Leader Respaldo",
        "totalDonations": 0,
        "totalReceived": 0,
        "memberList": [
            {
                "tag": "BACKUP1", 
                "name": "Datos de respaldo", 
                "donations": 0, 
                "donationsReceived": 0, 
                "trophies": 0, 
                "dailyDonations": 0,
                "dailyReceived": 0
            }
        ]
    }

def get_clan_data(clan_tag):
    """Obtiene datos del clan (cache o API)"""
    global clan_cache

    # Verificar cache (valido por 30 segundos para datos mas frescos)
    if clan_tag in clan_cache:
        cache_time = clan_cache[clan_tag]["timestamp"]
        if (datetime.now() - cache_time).seconds < 30:
            print(f"📋 Usando cache para clan #{clan_tag}")
            return clan_cache[clan_tag]["data"]

    # Obtener datos frescos de la API
    return get_clan_data_from_api(clan_tag)

def process_clans_ranking():
    """Procesa y ordena los clanes por donaciones totales"""
    print("🔄 Actualizando ranking de clanes...")
    clans = load_clans()
    ranking = []

    rank = 1
    for clan_tag, clan_name in clans.items():
        clan_data = get_clan_data(clan_tag)
        ranking.append({
            "rank": rank,
            "tag": clan_tag,
            "name": clan_data["name"],
            "leader": clan_data["leader"],
            "totalDonations": clan_data["totalDonations"],
            "totalReceived": clan_data["totalReceived"],
            "members": clan_data["members"]
        })
        rank += 1

    # Ordenar por donaciones totales (descendente)
    ranking.sort(key=lambda x: x["totalDonations"], reverse=True)

    # Reajustar rankings despues del ordenamiento
    for i, clan in enumerate(ranking):
        clan["rank"] = i + 1

    global last_update
    last_update = datetime.now()

    print(f"✅ Ranking actualizado - {len(ranking)} clanes procesados")
    return ranking

def daily_reset_worker():
    """Hilo dedicado exclusivamente a verificar el reset diario"""
    print("⏰ Iniciando monitor de reset diario (2 AM Argentina)...")
    
    last_check_date = None
    
    while True:
        try:
            # Verificar cada 5 minutos
            time.sleep(300)
            
            # Obtener tiempo actual en Argentina
            argentina_tz = timezone(timedelta(hours=-3))
            now_argentina = datetime.now(argentina_tz)
            current_date = now_argentina.date()
            
            # Solo verificar una vez por día
            if last_check_date == current_date:
                continue
            
            # Solo actuar entre las 2:00 y 2:30 AM
            if 2 <= now_argentina.hour <= 2 and now_argentina.minute <= 30:
                print(f"🌙 Verificando reset - {now_argentina.strftime('%H:%M:%S')}")
                
                if check_daily_reset():
                    last_check_date = current_date
                    print(f"✅ Reset completado para {current_date}")
                    
                    # Esperar 1 hora después del reset para evitar repeticiones
                    time.sleep(3600)
                    
        except Exception as e:
            print(f"❌ Error en monitor de reset: {e}")
            # En caso de error, esperar 10 minutos antes de intentar de nuevo
            time.sleep(600)

def auto_backup_worker():
    """Hilo que hace respaldo automático cada 2 minutos"""
    print("💾 Iniciando sistema de respaldo automático cada 2 minutos...")
    
    backup_counter = 0
    while True:
        try:
            time.sleep(120)  # 2 minutos
            backup_counter += 1
            
            # Solo hacer respaldo si hay datos que guardar
            if len(daily_stats_cache) > 0:
                print(f"💾 Respaldo automático #{backup_counter}...")
                if save_daily_donations():
                    print(f"✅ Respaldo #{backup_counter} guardado exitosamente")
                else:
                    print(f"❌ Error en respaldo #{backup_counter}")
            
        except Exception as e:
            print(f"❌ Error en sistema de respaldo: {e}")
            time.sleep(300)  # Esperar 5 minutos si hay error

def auto_update_worker():
    """Hilo que actualiza automáticamente cada 30 segundos"""
    print("🤖 Iniciando actualizador automático...")
    update_counter = 0
    
    while True:
        try:
            time.sleep(30)  # 30 segundos
            update_counter += 1
            
            print(f"⏰ Ejecutando actualización automática #{update_counter}...")

            # Limpiar cache viejo
            global clan_cache
            current_time = datetime.now()
            clan_cache = {
                tag: data for tag, data in clan_cache.items()
                if (current_time - data["timestamp"]).seconds < 300  # 5 minutos max
            }

            # Forzar actualización del ranking
            try:
                ranking = process_clans_ranking()
                print(f"✅ Actualización #{update_counter} completada - {len(ranking)} clanes")
            except Exception as e:
                print(f"❌ Error en actualización #{update_counter}: {e}")

        except Exception as e:
            print(f"❌ Error en actualización automática: {e}")
            time.sleep(120)  # Esperar 2 minutos si hay error

# Página HTML modificada según las especificaciones
HTML_PAGE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
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
            font-size: 14px;
            line-height: 1.4;
        }
        
        .header {
            background: #1a1a1a;
            color: white;
            padding: 8px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-size: 16px;
            font-weight: bold;
        }
        
        .logo .top { color: #ff6b35; }
        .logo .req { color: #ff1744; }
        .logo .clans { color: #ff6b35; }
        
        .container {
            max-width: 100%;
            margin: 0;
            background: white;
            min-height: calc(100vh - 50px);
        }
        
        .main-view {
            padding: 10px;
        }
        
        .page-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }
        
        .update-info {
            font-size: 11px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .api-status, .persistence-status {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 6px 8px;
            border-radius: 4px;
            font-size: 10px;
            margin-bottom: 8px;
            border-left: 3px solid #4caf50;
        }
        
        .clans-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-radius: 6px;
            overflow: hidden;
            font-size: 12px;
            border: 1px solid #dee2e6;
        }
        
        .clans-table th {
            background: #f8f9fa;
            padding: 8px 4px;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            border-right: 1px solid #dee2e6;
            font-size: 11px;
            color: #495057;
        }
        
        .clans-table th:last-child {
            border-right: none;
        }
        
        .clans-table td {
            padding: 6px 4px;
            border-bottom: 1px solid #f1f1f1;
            border-right: 1px solid #f1f1f1;
            vertical-align: middle;
            font-size: 11px;
        }
        
        .clans-table td:last-child {
            border-right: none;
        }
        
        .clans-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .clans-table tr:hover {
            background: #e3f2fd;
            cursor: pointer;
        }
        
        .auto-refresh {
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: #6c5ce7;
            color: white;
            padding: 6px 10px;
            border-radius: 15px;
            font-size: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        
        /* ESTILOS PARA LA VISTA DE DETALLE */
        .clan-detail-view {
            padding: 10px;
        }
        
        .back-button {
            background: #6c5ce7;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 15px;
            font-size: 12px;
        }
        
        .clan-header {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        
        .clan-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        /* NUEVA SECCIÓN DE INFORMACIÓN DEL CLAN CON CONTADORES */
        .clan-info-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border: 1px solid #dee2e6;
        }
        
        .daily-counters {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .counter-item {
            font-size: 13px;
            font-weight: 500;
            color: #333;
        }
        
        .counter-number {
            font-weight: bold;
            color: #2e7d32;
            margin-left: 5px;
        }
        
        .clan-basic-info {
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 12px;
            color: #666;
            text-align: right;
        }
        
        .time-until-reset {
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-bottom: 15px;
            padding: 8px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
        }

        .tab-buttons {
            display: flex;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            overflow: hidden;
            gap: 1px;
        }
        
        .tab-button {
            flex: 1;
            padding: 6px 2px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 9px;
            font-weight: 500;
            transition: all 0.2s ease;
            text-align: center;
        }
        
        .tab-button.active {
            background: #6c5ce7;
            color: white;
        }
        
        .tab-button.reset-btn {
            background: #ff6b35 !important;
            color: white !important;
        }
        
        .players-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-radius: 6px;
            overflow: hidden;
            font-size: 11px;
            border: 1px solid #dee2e6;
        }
        
        .players-table th {
            background: #f8f9fa;
            padding: 8px 4px;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            border-right: 1px solid #dee2e6;
            font-size: 10px;
        }
        
        .players-table th:last-child {
            border-right: none;
        }
        
        .players-table td {
            padding: 6px 4px;
            border-bottom: 1px solid #f1f1f1;
            border-right: 1px solid #f1f1f1;
            text-align: center;
            font-size: 10px;
        }
        
        .players-table td:last-child {
            border-right: none;
        }
        
        .players-table td:nth-child(2) {
            text-align: left;
            padding-left: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .players-table tr:nth-child(even) {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">
            <span class="top">TOP</span> <span class="req">REQ</span> <span class="clans">CLANS</span>
        </div>
    </header>
    
    <div class="container">
        <div class="main-view" id="mainView">
            <h1 class="page-title">Top Req Clans - Current season</h1>
            <div class="api-status">🟢 Conectado a la API oficial de Clash of Clans</div>
            <div class="persistence-status">💾 Sistema de persistencia activado - Reset automático 2 AM</div>
            <p class="update-info">Datos actualizados automáticamente cada 30s (Última actualización: <span id="lastUpdate">Cargando...</span>)</p>
            
            <table class="clans-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Clan</th>
                        <th>Leader</th>
                        <th>Donaciones</th>
                        <th>Recibidas</th>
                    </tr>
                </thead>
                <tbody id="clansTableBody">
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 20px;">
                            Cargando datos...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- VISTA DE DETALLE DEL CLAN MODIFICADA -->
        <div class="clan-detail-view" id="clanDetailView" style="display: none;">
            <button class="back-button" onclick="showMainView()">← Back to Clans</button>
            
            <div class="clan-header">
                <div class="clan-name" id="detailClanName">req n go</div>
            </div>

            <!-- NUEVA SECCIÓN CON CONTADORES A LA IZQUIERDA E INFO DEL CLAN A LA DERECHA -->
            <div class="clan-info-section">
                <div class="daily-counters">
                    <div class="counter-item">
                        Donaciones diarias:<span class="counter-number" id="totalDailyDonations">57,563</span>
                    </div>
                    <div class="counter-item">
                        Tropas diarias recibidas:<span class="counter-number" id="totalDailyReceived">38,409</span>
                    </div>
                </div>
                
                <div class="clan-basic-info">
                    <span>Leader: <span id="detailLeader">Foxx</span></span>
                    <span>Members: <span id="detailMembers">43</span></span>
                    <span>Total Donations: <span id="detailTotalDonations">3,926,074</span></span>
                </div>
            </div>

            <!-- TIEMPO HASTA RESET -->
            <div class="time-until-reset">
                Tiempo restante hasta que se restablezcan las donaciones diarias => <span id="timeUntilReset">10:54:22</span>
            </div>
            
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showPlayersTab('total')" id="totalDonationsBtn">
                    Temporada
                </button>
                <button class="tab-button" onclick="showPlayersTab('daily')" id="dailyDonationsBtn">
                    Hoy
                </button>
                <button class="tab-button reset-btn" onclick="resetDailyStats()" id="resetBtn">
                    Reset
                </button>
            </div>
            
            <table class="players-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Player</th>
                        <th>Don.</th>
                        <th>Rec.</th>
                        <th>Trofeos</th>
                    </tr>
                </thead>
                <tbody id="playersTableBody">
                    <!-- Los jugadores se cargarán aquí -->
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="auto-refresh" id="autoRefresh">
        🔄 <span id="countdown">30</span>s
    </div>

    <script>
        var currentData = {};
        var currentView = 'total';
        var selectedClanTag = '';
        var refreshInterval;
        var countdownInterval;
        var secondsLeft = 30;

        function formatNumber(num) {
            if (typeof num !== 'number') {
                num = parseInt(num) || 0;
            }
            return num.toLocaleString();
        }

        function updateLastUpdateTime() {
            var argentina = new Date().toLocaleString("es-AR", {
                timeZone: "America/Argentina/Buenos_Aires",
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
            document.getElementById('lastUpdate').textContent = argentina;
        }

        function startCountdown() {
            countdownInterval = setInterval(function() {
                secondsLeft--;
                document.getElementById('countdown').textContent = secondsLeft;
                if (secondsLeft <= 0) {
                    secondsLeft = 30;
                }
            }, 1000);
        }

        function updateDailyCounters(data) {
            console.log('📊 Actualizando contadores diarios...');
            
            // Cargar resumen diario del clan
            fetch('/api/clan/' + encodeURIComponent(selectedClanTag) + '/daily-summary', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            })
            .then(function(response) { return response.json(); })
            .then(function(dailySummary) {
                // Actualizar contadores simples
                document.getElementById('totalDailyDonations').textContent = formatNumber(dailySummary.total_daily_donations);
                document.getElementById('totalDailyReceived').textContent = formatNumber(dailySummary.total_daily_received);
                document.getElementById('timeUntilReset').textContent = dailySummary.time_until_reset;
                
                console.log('✅ Contadores diarios actualizados');
            })
            .catch(function(error) {
                console.error('❌ Error cargando resumen diario:', error);
            });
        }

        function showClanDetail(clanTag) {
            selectedClanTag = clanTag;
            console.log('🔍 Cargando detalles del clan:', clanTag);
            
            fetch('/api/clan/' + encodeURIComponent(clanTag), {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                console.log('📋 Datos del clan cargados:', data.name, data.memberList.length, 'miembros');
                currentData = data;
                
                document.getElementById('mainView').style.display = 'none';
                document.getElementById('clanDetailView').style.display = 'block';
                
                document.getElementById('detailClanName').textContent = data.name;
                document.getElementById('detailLeader').textContent = data.leader;
                document.getElementById('detailMembers').textContent = data.members;
                document.getElementById('detailTotalDonations').textContent = formatNumber(data.totalDonations);
                
                // Actualizar los nuevos contadores diarios
                updateDailyCounters(data);
                
                showPlayersTab('total');
            })
            .catch(function(error) {
                console.error('❌ Error loading clan details:', error);
            });
        }

        function showMainView() {
            document.getElementById('mainView').style.display = 'block';
            document.getElementById('clanDetailView').style.display = 'none';
            selectedClanTag = '';
        }

        function showPlayersTab(tabType) {
            currentView = tabType;
            console.log('🔄 Cambiando a tab:', tabType);
            
            document.getElementById('totalDonationsBtn').classList.remove('active');
            document.getElementById('dailyDonationsBtn').classList.remove('active');
            document.getElementById(tabType === 'total' ? 'totalDonationsBtn' : 'dailyDonationsBtn').classList.add('active');

            if (!currentData.memberList) {
                return;
            }

            var players = currentData.memberList.slice();
            players.sort(function(a, b) {
                var aValue, bValue;
                if (tabType === 'total') {
                    aValue = a.donations || 0;
                    bValue = b.donations || 0;
                } else {
                    aValue = (a.dailyDonations || 0) + (a.dailyReceived || 0);
                    bValue = (b.dailyDonations || 0) + (b.dailyReceived || 0);
                }
                return bValue - aValue;
            });

            var tbody = document.getElementById('playersTableBody');
            tbody.innerHTML = '';

            players.forEach(function(player, index) {
                var donations, received;
                
                if (tabType === 'total') {
                    donations = player.donations || 0;
                    received = player.donationsReceived || 0;
                } else {
                    donations = player.dailyDonations || 0;
                    received = player.dailyReceived || 0;
                }

                var row = document.createElement('tr');
                row.innerHTML = 
                    '<td style="text-align: center; font-weight: bold;">' + (index + 1) + '</td>' +
                    '<td style="text-align: left; font-weight: 500;">' + player.name + '</td>' +
                    '<td style="text-align: center; font-weight: 600; color: #2e7d32;">' + formatNumber(donations) + '</td>' +
                    '<td style="text-align: center; font-weight: 600; color: #d32f2f;">' + formatNumber(received) + '</td>' +
                    '<td style="text-align: center;">' + formatNumber(player.trophies) + '</td>';
                tbody.appendChild(row);
            });

            console.log('👥 Jugadores ordenados:', players.length, 'por', tabType);
        }

        function resetDailyStats() {
            if (confirm('¿Resetear todas las donaciones diarias a 0?')) {
                console.log('🔄 Ejecutando reset manual...');
                
                fetch('/api/reset-daily', {
                    method: 'GET',
                    headers: {
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    console.log('✅ Reset completado:', data);
                    alert('¡Reset completado! Las donaciones diarias empezarán desde 0.');
                    
                    if (selectedClanTag) {
                        showClanDetail(selectedClanTag);
                    }
                })
                .catch(function(error) {
                    console.error('❌ Error en reset:', error);
                    alert('Error al hacer reset.');
                });
            }
        }

        function loadClansRanking() {
            console.log('📡 Cargando ranking de clanes...');
            
            fetch('/api/ranking', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            })
            .then(function(response) { 
                return response.json(); 
            })
            .then(function(ranking) {
                var tbody = document.getElementById('clansTableBody');
                tbody.innerHTML = '';
                
                ranking.forEach(function(clan) {
                    var row = document.createElement('tr');
                    row.style.cursor = 'pointer';
                    row.onclick = function() { showClanDetail(clan.tag); };
                    
                    row.innerHTML = 
                        '<td style="text-align: center; font-weight: bold;">' + clan.rank + '</td>' +
                        '<td style="font-weight: 600;">' + clan.name + '<br><small style="color: #666;">#' + clan.tag + '</small></td>' +
                        '<td style="text-align: center;">' + clan.leader + '</td>' +
                        '<td style="text-align: center; color: #2e7d32; font-weight: 600;">' + formatNumber(clan.totalDonations) + '</td>' +
                        '<td style="text-align: center; color: #d32f2f; font-weight: 600;">' + formatNumber(clan.totalReceived) + '</td>';
                    
                    tbody.appendChild(row);
                });

                updateLastUpdateTime();
                secondsLeft = 30;
                console.log('✅ Ranking cargado:', ranking.length, 'clanes');
            })
            .catch(function(error) {
                console.error('❌ Error loading clans:', error);
                var tbody = document.getElementById('clansTableBody');
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: red;">Error cargando datos</td></tr>';
            });
        }

        function startAutoRefresh() {
            refreshInterval = setInterval(function() {
                console.log('⏰ Auto-refresh ejecutándose...');
                if (document.getElementById('mainView').style.display !== 'none') {
                    loadClansRanking();
                } else if (selectedClanTag) {
                    showClanDetail(selectedClanTag);
                }
            }, 30000);
        }

        window.onload = function() { 
            console.log('🚀 Aplicación iniciada');
            loadClansRanking();
            startAutoRefresh();
            startCountdown();
        };

        window.onbeforeunload = function() {
            if (refreshInterval) clearInterval(refreshInterval);
            if (countdownInterval) clearInterval(countdownInterval);
        };
    </script>
</body>
</html>'''

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(HTML_PAGE.encode('utf-8'))
                
            elif self.path == '/api/ranking':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                ranking = process_clans_ranking()
                self.wfile.write(json.dumps(ranking, ensure_ascii=False).encode('utf-8'))
                
            elif self.path.startswith('/api/clan/') and self.path.endswith('/daily-summary'):
                # Endpoint para el resumen diario
                clan_tag = urllib.parse.unquote(self.path.split('/')[-2])
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                daily_summary = get_clan_daily_summary(clan_tag)
                self.wfile.write(json.dumps(daily_summary, ensure_ascii=False).encode('utf-8'))
                
            elif self.path.startswith('/api/clan/'):
                clan_tag = urllib.parse.unquote(self.path.split('/')[-1])
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                clan_data = get_clan_data(clan_tag)
                self.wfile.write(json.dumps(clan_data, ensure_ascii=False).encode('utf-8'))
                
            elif self.path == '/api/reset-daily':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                success = force_daily_reset()
                response = {'success': success, 'message': 'Reset completado' if success else 'Error en reset'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'404 - Not Found')
                
        except Exception as e:
            print(f"❌ Error en request handler: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

def check_port_availability(port):
    """Verifica si el puerto está disponible"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False

def find_available_port(start_port=8000):
    """Encuentra un puerto disponible empezando desde start_port"""
    port = start_port
    while port < start_port + 100:
        if check_port_availability(port):
            return port
        port += 1
    return None

def main():
    """Función principal del servidor"""
    global PORT
    
    print("🚀 Iniciando TOP REQ CLANS Server...")
    print("=" * 50)
    
    # Cargar estadísticas guardadas
    load_daily_donations()
    
    # Verificar disponibilidad del puerto
    if not check_port_availability(PORT):
        print(f"⚠️ Puerto {PORT} ocupado, buscando puerto alternativo...")
        alt_port = find_available_port(PORT)
        if alt_port:
            PORT = alt_port
            print(f"✅ Usando puerto alternativo: {PORT}")
        else:
            print("❌ No se encontró puerto disponible")
            return
    
    # Inicializar hilos de trabajo
    print("🔧 Inicializando sistemas automáticos...")
    
    # Hilo para reset diario automático
    reset_thread = threading.Thread(target=daily_reset_worker, daemon=True)
    reset_thread.start()
    print("✅ Monitor de reset diario iniciado")
    
    # Hilo para respaldos automáticos
    backup_thread = threading.Thread(target=auto_backup_worker, daemon=True)
    backup_thread.start()
    print("✅ Sistema de respaldo automático iniciado")
    
    # Hilo para actualizaciones automáticas
    update_thread = threading.Thread(target=auto_update_worker, daemon=True)
    update_thread.start()
    print("✅ Actualizador automático iniciado")
    
    print("=" * 50)
    
    try:
        # Configurar y iniciar servidor HTTP
        with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
            httpd.allow_reuse_address = True
            
            # Obtener IP local
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            print(f"🌐 Servidor ejecutándose en:")
            print(f"   • Local: http://localhost:{PORT}")
            print(f"   • Red:   http://{local_ip}:{PORT}")
            print(f"   • Puerto: {PORT}")
            print("=" * 50)
            print("📊 Características del sistema:")
            print("   • ✅ API oficial de Clash of Clans")
            print("   • ✅ Persistencia de datos automática")
            print("   • ✅ Reset automático a las 2 AM (Argentina)")
            print("   • ✅ Respaldo cada 2 minutos")
            print("   • ✅ Actualización cada 30 segundos")
            print("   • ✅ Interfaz web responsive")
            print("=" * 50)
            print("💡 Presiona Ctrl+C para detener el servidor")
            print("🔄 Estado: EJECUTÁNDOSE...")
            
            # Hacer una actualización inicial
            print("\n📡 Realizando carga inicial de datos...")
            try:
                ranking = process_clans_ranking()
                print(f"✅ Datos iniciales cargados: {len(ranking)} clanes")
            except Exception as e:
                print(f"⚠️ Error en carga inicial: {e}")
            
            print("\n🎯 El servidor está listo para recibir conexiones\n")
            
            # Iniciar servidor
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Cerrando servidor...")
        
        # Guardar datos antes de cerrar
        print("💾 Guardando datos finales...")
        if save_daily_donations():
            print("✅ Datos guardados exitosamente")
        else:
            print("⚠️ Error guardando datos finales")
            
        print("👋 ¡Servidor cerrado correctamente!")
        
    except Exception as e:
        print(f"❌ Error fatal del servidor: {e}")
        
        # Intentar guardar datos de emergencia
        try:
            save_daily_donations()
            print("💾 Datos de emergencia guardados")
        except:
            print("❌ No se pudieron guardar datos de emergencia")

if __name__ == "__main__":
    main()
