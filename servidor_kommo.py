from flask import Flask, request, jsonify
import requests
import random
import string
import gzip
import os
import json

app = Flask(__name__)

# ============================================================
#  CONFIGURACION
# ============================================================
PANEL_URL     = "https://admin.goldenclub.pro/index.php"
API_USER      = "eliteadmin"
API_PASS      = "GolElite99"
HALL_ID       = "6875291"
GROUP_ID      = "5"
PASS_DEFAULT  = "hola1234"

KOMMO_DOMAIN  = "feria4131.kommo.com"
KOMMO_TOKEN   = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImMwZmNmMWQ5NDEzOTZmOTU2ZTQ1ODEzZjQ1ZmQ1NjM4NGVkOTRiMjEyODg1ZDg3YmNiOGIwMzI5YjBiMjI1NzZmMGJhOGMxNzk3YmYwODU5In0.eyJhdWQiOiJkNDUyNmZmMi04MjMxLTRiMWQtYjQ2ZC03MTRmYTQwN2JiNGUiLCJqdGkiOiJjMGZjZjFkOTQxMzk2Zjk1NmU0NTgxM2Y0NWZkNTYzODRlZDk0YjIxMjg4NWQ4N2JjYjhiMDMyOWIwYjIyNTc2ZjBiYThjMTc5N2JmMDg1OSIsImlhdCI6MTc3NzI2MDEwMCwibmJmIjoxNzc3MjYwMTAwLCJleHAiOjE4MzAyMTEyMDAsInN1YiI6IjE0OTY0MDgzIiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjM2MjE0MDM1LCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJmaWxlcyIsImNybSIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiY2E2NWRjNWYtNDVmMi00YWZjLTg2YzUtNjY0NDg3MWE1Njg0IiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.EkaktT8SMVuc2MnvGxg_LX1pXa9H5fg2dL2BnXorxXKKhKdnrgo3NKQgywIhJOy5CLYH9M0QERgT5Ei30zaEGY8YRjfJpIcpgNrh34Hy7-NmU1z2OTeXHsmUAlY4G-Ui_ksio3-tnF93of6ulmubU1KZ7P63R0FzLygUZiYt601L0r2gMlGgAqzUN_MRF_R4PL1kof0AhTuvjNjV2IWRRt3E3Yk8Fjp1Y60KWDS5qBpaoqLLynk6q1D3II49gi7dcUwpULxZQdP4uX9Sir1nNCcCfpgmP_MLzU47eNduiSDki7KxvFsR_mmDBkH_YcWvbc4J0t4M5xTTyhvA3EBpJg"

CAMPO_USUARIO    = 2617607
CAMPO_CONTRASENA = 2617609
# ============================================================

def generar_login():
    letras  = ''.join(random.choices(string.ascii_lowercase, k=6))
    numeros = ''.join(random.choices(string.digits, k=4))
    return letras + numeros

def decode_response(resp):
    content = resp.content
    try:
        content = gzip.decompress(content)
    except:
        pass
    try:
        return content.decode('utf-8')
    except:
        return content.decode('latin-1', errors='replace')

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "es-US,es;q=0.9",
        "Origin": "https://admin.goldenclub.pro",
    })
    login_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://admin.goldenclub.pro/index.php?act=admin&area=login",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
    }
    payload = {"login": API_USER, "password": API_PASS}
    params  = {"act": "admin", "area": "login"}
    resp = session.post(PANEL_URL, params=params, data=payload,
                        headers=login_headers, timeout=10, allow_redirects=True)
    print(f"[login] Status: {resp.status_code} | Cookies: {dict(session.cookies)}")
    return session

def crear_usuario():
    try:
        login   = generar_login()
        session = get_session()
        ajax_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "identity",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://admin.goldenclub.pro/index.php",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        payload = {
            "group":    GROUP_ID,
            "sended":   "true",
            "login":    login,
            "password": PASS_DEFAULT,
            "balance":  ""
        }
        params = {
            "act":  "admin",
            "area": "createuser",
            "id":   HALL_ID
        }
        resp = session.post(PANEL_URL, params=params, data=payload,
                            headers=ajax_headers, timeout=15)
        text = decode_response(resp)
        print(f"[crear_usuario] Respuesta: {text[:300]}")

        if "xito" in text or "Exito" in text:
            return {"ok": True, "login": login, "password": PASS_DEFAULT}

        try:
            data = json.loads(text)
            error_msg = data.get("errorMessage") or data.get("error") or ""
            if data.get("status") == "success":
                return {"ok": True, "login": login, "password": PASS_DEFAULT}
            elif "existe" in str(error_msg).lower() or "busy" in str(error_msg).lower():
                return crear_usuario()
            else:
                return {"ok": False, "error": str(error_msg) or "Error desconocido"}
        except:
            return {"ok": False, "error": f"Respuesta inesperada: {text[:100]}"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def guardar_credenciales_en_lead(lead_id, login, password):
    """Guarda las credenciales en los campos personalizados del lead en Kommo"""
    try:
        headers = {
            "Authorization": f"Bearer {KOMMO_TOKEN}",
            "Content-Type": "application/json"
        }
        url = f"https://{KOMMO_DOMAIN}/api/v4/leads"
        payload = [{
            "id": int(lead_id),
            "custom_fields_values": [
                {"field_id": CAMPO_USUARIO,    "values": [{"value": login}]},
                {"field_id": CAMPO_CONTRASENA, "values": [{"value": password}]}
            ]
        }]
        resp = requests.patch(url, headers=headers, json=payload, timeout=10)
        print(f"[campos] Status: {resp.status_code} | Resp: {resp.text[:200]}")
        return resp.status_code in [200, 201]
    except Exception as e:
        print(f"[campos] Error: {e}")
        return False


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        raw = request.get_data(as_text=True)
        print(f"[webhook] RAW: {raw[:500]}")

        form_data = request.form
        lead_id = (form_data.get("leads[add][0][id]") or
                   form_data.get("leads[update][0][id]") or
                   form_data.get("leads[status][0][id]"))

        print(f"[webhook] Lead ID: {lead_id}")

        resultado = crear_usuario()

        if resultado["ok"]:
            login    = resultado["login"]
            password = resultado["password"]
            print(f"[webhook] Usuario creado: {login}")

            if lead_id:
                guardar_credenciales_en_lead(lead_id, login, password)

            return jsonify({"status": "ok", "login": login, "password": password})
        else:
            print(f"[webhook] Error: {resultado['error']}")
            return jsonify({"status": "error", "detalle": resultado["error"]})

    except Exception as e:
        print(f"[webhook] Error general: {e}")
        return jsonify({"status": "error", "detalle": str(e)}), 500


@app.route('/test_crear_usuario', methods=['GET'])
def test_crear():
    resultado = crear_usuario()
    return jsonify(resultado)


@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "mensaje": "Servidor Casino activo"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
