from flask import Flask, request, jsonify
import requests
import hashlib
import datetime
import json
import os

app = Flask(__name__)

# ============================================================
#  CONFIGURACION
# ============================================================
PANEL_URL  = "https://admin.goldenclub.pro/index.php"
API_TOKEN  = "2972bcc76bf82a575eaf3cab11c6c9f33e2784ddb692ee1ecd6905aac1cbeae1"
HALL_ID    = "6875291"
KOMMO_URL  = "https://feria4131.kommo.com"
# ============================================================

def calcular_mac(token, hall_id):
    return hashlib.md5((token + hall_id).encode()).hexdigest()

def calcular_terminal(login, password):
    return hashlib.md5((login + password).encode()).hexdigest()

def calcular_key(hall_id, login):
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "DEC"
    return f"{hall_id}_{login}_{now}"

# ================================================================
#  FUNCIONES DE LA API DEL PANEL
# ================================================================

def crear_usuario():
    """Crea un usuario tipo terminal con PIN automatico"""
    mac = calcular_mac(API_TOKEN, HALL_ID)
    payload = {
        "cmd": "terminalCreate",
        "hall_id": HALL_ID,
        "mac": mac,
        "terminal": "OK"
    }
    try:
        resp = requests.post(
            f"{PANEL_URL}?act=admin&area=cmd&response=js&token={API_TOKEN}",
            json=payload,
            timeout=10
        )
        data = resp.json()
        print(f"[crear_usuario] Respuesta: {data}")
        if data.get("status") == "success":
            return {
                "ok": True,
                "login": data["content"]["login"],
                "password": data["content"]["password"],
                "id": data["content"]["id"]
            }
        else:
            return {"ok": False, "error": data.get("error", "Error desconocido")}
    except Exception as e:
        print(f"[crear_usuario] Error: {e}")
        return {"ok": False, "error": str(e)}

def depositar_usuario(login, password, monto):
    """Deposita saldo a un usuario"""
    mac  = calcular_mac(API_TOKEN, HALL_ID)
    term = calcular_terminal(login, password)
    key  = calcular_key(HALL_ID, login)
    payload = {
        "cmd": "terminalCash",
        "operation": "in",
        "cash": str(monto),
        "hall_id": HALL_ID,
        "mac": mac,
        "key": key,
        "terminal": term
    }
    try:
        resp = requests.post(
            f"{PANEL_URL}?act=admin&area=cmd&response=js&token={API_TOKEN}",
            json=payload,
            timeout=10
        )
        data = resp.json()
        print(f"[depositar_usuario] Respuesta: {data}")
        if data.get("status") == "success":
            return {
                "ok": True,
                "saldo": data["content"]["cash"],
                "operacion_id": data["content"]["operationId"]
            }
        else:
            return {"ok": False, "error": data.get("error", "Error desconocido")}
    except Exception as e:
        print(f"[depositar_usuario] Error: {e}")
        return {"ok": False, "error": str(e)}

def info_usuario(login, password):
    """Obtiene info de un usuario"""
    mac  = calcular_mac(API_TOKEN, HALL_ID)
    term = calcular_terminal(login, password)
    payload = {
        "cmd": "terminalInfo",
        "hall_id": HALL_ID,
        "mac": mac,
        "terminal": term
    }
    try:
        resp = requests.post(
            f"{PANEL_URL}?act=admin&area=cmd&response=js&token={API_TOKEN}",
            json=payload,
            timeout=10
        )
        data = resp.json()
        if data.get("status") == "success":
            return {"ok": True, "data": data["content"]}
        else:
            return {"ok": False, "error": data.get("error")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ================================================================
#  WEBHOOK — recibe eventos de Kommo
# ================================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Kommo manda los datos del lead cuando el bot termina de recopilarlos.
    El payload esperado es:
    {
        "accion": "crear_usuario" | "carga",
        "lead_id": "123456",
        "nombre": "Juan",
        "monto": "5000"       (solo para carga)
    }
    """
    try:
        data = request.get_json(force=True)
        print(f"[webhook] Recibido: {data}")

        accion   = data.get("accion", "")
        lead_id  = data.get("lead_id", "")
        nombre   = data.get("nombre", "Usuario")
        monto    = data.get("monto", "0")

        if accion == "crear_usuario":
            resultado = crear_usuario()
            if resultado["ok"]:
                mensaje = (
                    f"✅ ¡Tu cuenta fue creada exitosamente!\n\n"
                    f"👤 *Usuario:* `{resultado['login']}`\n"
                    f"🔐 *Contraseña:* `{resultado['password']}`\n\n"
                    f"Ingresá con estos datos en la plataforma. "
                    f"¡Mucha suerte! 🎰"
                )
                enviar_mensaje_kommo(lead_id, mensaje)
                return jsonify({"status": "ok", "login": resultado["login"]})
            else:
                enviar_mensaje_kommo(lead_id,
                    "❌ Hubo un error al crear tu cuenta. Un asesor te va a contactar en breve.")
                return jsonify({"status": "error", "detalle": resultado["error"]})

        elif accion == "carga":
            # Para carga, derivar a humano con los datos recopilados
            mensaje_interno = (
                f"💰 *Solicitud de carga*\n"
                f"Nombre: {nombre}\n"
                f"Monto solicitado: ${monto}\n"
                f"⚠️ Requiere aprobación manual."
            )
            enviar_nota_interna_kommo(lead_id, mensaje_interno)
            enviar_mensaje_kommo(lead_id,
                "✅ Recibimos tu solicitud de carga. Un asesor la va a confirmar en breve.")
            return jsonify({"status": "ok"})

        else:
            return jsonify({"status": "error", "detalle": "Accion desconocida"})

    except Exception as e:
        print(f"[webhook] Error general: {e}")
        return jsonify({"status": "error", "detalle": str(e)}), 500


def enviar_mensaje_kommo(lead_id, texto):
    """Envia un mensaje al lead en Kommo via API"""
    # TODO: completar con el token de Kommo cuando este disponible
    print(f"[Kommo] Mensaje para lead {lead_id}: {texto}")

def enviar_nota_interna_kommo(lead_id, texto):
    """Agrega una nota interna en el lead de Kommo"""
    print(f"[Kommo] Nota interna para lead {lead_id}: {texto}")


# ================================================================
#  HEALTH CHECK
# ================================================================
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "mensaje": "Servidor Casino activo"})

@app.route('/test_crear_usuario', methods=['GET'])
def test_crear():
    """Endpoint de prueba para verificar que la API del panel funciona"""
    resultado = crear_usuario()
    return jsonify(resultado)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
