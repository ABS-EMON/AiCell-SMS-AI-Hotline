import serial
import threading
import time
import requests
import re
from flask import Flask, jsonify, request
import logging
import socket
import serial.tools.list_ports

# ============================= CONFIG =============================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aicell.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# === OPENROUTER API (Optional - fallback works without it) ===
OPENROUTER_API_KEY = "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"  # Leave as-is for fallback
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# === GSM CONFIG ===
GSM_NUMBER = "+8801833890003"
BAUD_RATE = 115200
SERIAL_TIMEOUT = 5
gsm_serial = None

# === PREDEFINED RESPONSES ===
PREDEFINED_RESPONSES = {
    "hi": "Hello! This is AiCell - your AI-powered SMS assistant.",
    "hello": "Hello! This is AiCell - your AI-powered SMS assistant.",
    "about aicell": "AiCell is an AI-based SMS hotline that provides smart replies without internet. Ask me anything!",
    "help": "Just send your question. I can help with education, health, agriculture, and general info.",
    "info": "AiCell: AI via SMS. No internet needed. Free service.",
    "thanks": "You're welcome! Happy to help.",
    "thank you": "You're welcome! Feel free to ask more questions.",
    "what is aicell": "AiCell is an AI SMS hotline that gives smart replies without internet. Just text me any question!",
    "who are you": "I'm AiCell, your AI SMS assistant. I can help with information, education, health tips, and more!",
}


# ==================================================================
# =========================== SERIAL HELPERS =======================
# ==================================================================

def list_available_ports():
    """List all available COM ports"""
    ports = serial.tools.list_ports.comports()
    available = []
    print("\nAvailable COM ports:")
    for p in ports:
        print(f"  {p.device} - {p.description}")
        available.append(p.device)
    return available


def find_gsm_port():
    """Auto-find GSM module"""
    possible = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM10']
    for port in possible:
        try:
            print(f"Trying {port}...")
            ser = serial.Serial(port, BAUD_RATE, timeout=2)
            time.sleep(2)
            ser.write(b'AT\r\n')
            time.sleep(1)
            resp = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            ser.close()
            if "OK" in resp:
                print(f"GSM Module FOUND on {port}")
                return port
        except:
            continue
    print("GSM module NOT found. Check connections.")
    return None


def safe_send_command(command, wait_time=3):
    """Send AT command and PRINT full response"""
    if not gsm_serial or not gsm_serial.is_open:
        return "GSM not connected"

    try:
        gsm_serial.flushInput()
        gsm_serial.flushOutput()

        print(f"\n>>> AT COMMAND: {command}")
        logging.debug(f"Sending: {command}")

        gsm_serial.write((command + "\r\n").encode())
        time.sleep(0.5)

        response = ""
        start = time.time()
        while (time.time() - start) < wait_time:
            if gsm_serial.in_waiting:
                chunk = gsm_serial.read(gsm_serial.in_waiting).decode('utf-8', errors='ignore')
                response += chunk
                for line in chunk.split('\n'):
                    line = line.strip()
                    if line:
                        print(f"<< {line}")
            time.sleep(0.1)

        return response
    except Exception as e:
        error_msg = f"Serial Error: {e}"
        print(f"ERROR: {error_msg}")
        return error_msg


# ==================================================================
# =========================== GSM INIT =============================
# ==================================================================

def init_gsm():
    global gsm_serial

    print("\nInitializing GSM Module...")
    port = find_gsm_port()
    if not port:
        return False

    try:
        gsm_serial = serial.Serial(port, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        time.sleep(3)

        # Test connection
        for i in range(3):
            resp = safe_send_command("AT", 3)
            if "OK" in resp:
                print("GSM is RESPONDING")
                break
            time.sleep(2)
        else:
            print("GSM not responding to AT")
            return False

        # Disable echo
        safe_send_command("ATE0", 2)

        # Check SIM
        resp = safe_send_command("AT+CPIN?", 3)
        if "READY" not in resp:
            print("SIM not ready. Trying common PINs...")
            for pin in ["0000", "1234", "1111"]:
                safe_send_command(f'AT+CPIN="{pin}"', 3)
                time.sleep(2)

        # Network registration
        print("Waiting for network...")
        for i in range(10):
            resp = safe_send_command("AT+CREG?", 5)
            if "+CREG: 0,1" in resp or "+CREG: 0,5" in resp:
                print("NETWORK REGISTERED")
                break
            print(f"  Still searching... ({i + 1}/10)")
            time.sleep(5)
        else:
            print("Network not registered, but continuing...")

        # Set SMS text mode
        safe_send_command("AT+CMGF=1", 2)

        # Try multiple CNMI modes
        cnmi_modes = [
            "AT+CNMI=2,2,0,0,0",
            "AT+CNMI=1,2,0,0,0",
            "AT+CNMI=2,1,0,0,0",
            "AT+CNMI=1,1,0,0,0"
        ]
        for mode in cnmi_modes:
            resp = safe_send_command(mode, 2)
            if "OK" in resp:
                print(f"SMS Indication: {mode}")
                break

        # Signal quality
        safe_send_command("AT+CSQ", 2)

        print(f"GSM READY: {GSM_NUMBER}")
        return True

    except Exception as e:
        print(f"GSM Init Failed: {e}")
        return False


# ==================================================================
# =========================== SMS HANDLING =========================
# ==================================================================

def send_sms(phone_number, message):
    """Send SMS with full terminal feedback"""
    try:
        print(f"\nSENDING SMS")
        print(f"TO  : {phone_number}")
        print(f"MSG : {message}")
        print("-" * 60)

        # Format number
        if not phone_number.startswith('+'):
            if phone_number.startswith('01') and len(phone_number) == 11:
                phone_number = '+88' + phone_number
            elif phone_number.startswith('8801'):
                phone_number = '+' + phone_number

        safe_send_command("AT+CMGF=1", 2)
        time.sleep(1)

        cmd = f'AT+CMGS="{phone_number}"'
        gsm_serial.write((cmd + "\r\n").encode())
        time.sleep(2)

        gsm_serial.write(message.encode('utf-8'))
        time.sleep(1)
        gsm_serial.write(bytes([26]))  # CTRL+Z
        time.sleep(3)

        resp = ""
        start = time.time()
        while time.time() - start < 15:
            if gsm_serial.in_waiting:
                resp += gsm_serial.read(gsm_serial.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.5)

        if "+CMGS:" in resp or "OK" in resp:
            print("SMS SENT SUCCESSFULLY!")
            logging.info(f"Sent to {phone_number}: {message}")
            return True
        else:
            print(f"SMS FAILED:\n{resp}")
            return False

    except Exception as e:
        print(f"SMS SEND ERROR: {e}")
        return False


def parse_incoming_sms(data):
    """Extract sender and message"""
    try:
        lines = [l.strip() for l in data.split('\n') if l.strip()]
        sender = None
        message = ""
        for i, line in enumerate(lines):
            if line.startswith('+CMT:'):
                parts = line.split('"')
                if len(parts) > 1:
                    sender = parts[1]
            elif sender and i > 0 and not line.startswith('+'):
                message = line
                if i + 1 < len(lines) and not lines[i + 1].startswith('+'):
                    message += " " + lines[i + 1]
                break
        return sender, message.strip(), ""
    except:
        return None, "", ""


def get_ai_response(user_message):
    """Get AI response or fallback"""
    clean = user_message.lower().strip()

    # Predefined
    if clean in PREDEFINED_RESPONSES:
        return PREDEFINED_RESPONSES[clean]
    for key in PREDEFINED_RESPONSES:
        if key in clean:
            return PREDEFINED_RESPONSES[key]

    # Fallback if no API key
    if OPENROUTER_API_KEY == "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":
        return "AiCell here! Ask about health, education, or farming."

    # OpenRouter AI
    try:
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "system", "content": "You are AiCell SMS bot. Reply in <140 chars. Simple Bangla/English."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 80
        }
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"]
            return text[:157] + "..." if len(text) > 160 else text
    except:
        pass

    return "Thanks for your message! I'll reply soon."


def process_sms(sender, message):
    """Process and reply"""
    try:
        clean = re.sub(r'[^\w\s\.\?\!]', '', message.lower().strip())
        print(f"\nPROCESSING: '{message}'")

        reply = get_ai_response(clean)
        if len(reply) > 160:
            reply = reply[:157] + "..."

        send_sms(sender, reply)
    except Exception as e:
        print(f"Process error: {e}")
        send_sms(sender, "Sorry, try again.")


# ==================================================================
# =========================== SMS MONITOR ==========================
# ==================================================================

def monitor_sms():
    """Monitor and PRINT all SMS"""
    print("\n" + "=" * 70)
    print("   AiCell SMS MONITOR ACTIVE")
    print(f"   Hotline: {GSM_NUMBER}")
    print("   Send 'hi' to test")
    print("=" * 70 + "\n")

    buffer = ""
    while True:
        try:
            if gsm_serial and gsm_serial.in_waiting:
                char = gsm_serial.read().decode('utf-8', errors='ignore')
                buffer += char

                if char == '\n':
                    line = buffer.strip()
                    buffer = ""

                    if line:
                        print(f"RAW: {line}")

                    if line.startswith('+CMT:'):
                        print("\n" + "!" * 60)
                        print("   NEW SMS RECEIVED!")
                        print("!" * 60)

                        full = line + "\n"
                        time.sleep(1)
                        while gsm_serial.in_waiting:
                            full += gsm_serial.read(gsm_serial.in_waiting).decode('utf-8', errors='ignore')

                        sender, msg, _ = parse_incoming_sms(full)
                        if sender and msg:
                            print(f"FROM: {sender}")
                            print(f"MSG : {msg}")
                            print("-" * 60)

                            threading.Thread(
                                target=process_sms,
                                args=(sender, msg),
                                daemon=True
                            ).start()
                        else:
                            print("Failed to parse SMS")
            else:
                time.sleep(0.1)

            # Health check
            if int(time.time()) % 30 == 0:
                safe_send_command("AT", 1)

        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(2)


# ==================================================================
# =========================== FLASK API ===========================
# ==================================================================

@app.route('/health')
def health():
    return jsonify({
        'status': 'AiCell Running',
        'gsm': gsm_serial.is_open if gsm_serial else False,
        'number': GSM_NUMBER,
        'time': time.strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/test_sms/<number>', methods=['POST'])
def test(number):
    data = request.get_json()
    msg = data.get('message', 'Test from AiCell')
    success = send_sms(number, msg)
    return jsonify({'success': success})


# ==================================================================
# =========================== MAIN ================================
# ==================================================================

def main():
    print("AiCell SMS AI Server Starting...")
    print(f"Hotline: {GSM_NUMBER}")
    print("=" * 60)

    if not init_gsm():
        print("\nGSM FAILED. Check:")
        print("  1. SIM card inserted?")
        print("  2. Antenna connected?")
        print("  3. LED blinking every 3 sec?")
        print("  4. Run as Administrator")
        list_available_ports()
        return

    # Start monitor
    threading.Thread(target=monitor_sms, daemon=True).start()

    # Find port
    def find_port(start=5000):
        for p in range(start, start + 100):
            with socket.socket() as s:
                try:
                    s.bind(('127.0.0.1', p))
                    return p
                except:
                    continue
        return 5000

    port = find_port()
    print(f"\nWeb Dashboard: http://127.0.0.1: {port}/health")
    print("SEND SMS NOW TO TEST!")
    print("=" * 60)

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()