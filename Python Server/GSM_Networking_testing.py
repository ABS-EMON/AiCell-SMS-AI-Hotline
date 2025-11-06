import serial
import time
import sys
import threading

# ==================== CONFIG ====================
PORT = 'COM3'             # Change if needed
BAUD_RATE = 115200          # SIM800C default
MY_PHONE = '+8801518979969'
AUTO_REPLY_MSG = 'I am Sim800C GSM module'
# ================================================

ser = None
lock = threading.Lock()  # Prevent serial access conflicts


def send_at(cmd, timeout_ms=1000, show_cmd=True):
    """Send an AT command and return the response."""
    if not ser:
        return ""
    with lock:
        if show_cmd:
            print(f"> {cmd}")
        ser.write((cmd + '\r\n').encode())
        ser.flush()

        time.sleep(timeout_ms / 1000.0)
        response = ""
        while ser.in_waiting:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.05)
        response = response.strip()
        if response:
            print(f"< {response}")
        return response


def init_modem():
    """Initialize the SIM800C modem safely."""
    global ser
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"Initializing SIM800C on {PORT}...")

        send_at("ATE0")  # Disable echo
        send_at("AT")    # Test connection
        time.sleep(0.5)

        # Wait for SIM ready
        for _ in range(5):
            resp = send_at("AT+CPIN?", 1000)
            if "READY" in resp:
                print("SIM Ready detected.")
                break
            print("Waiting for SIM to be ready...")
            time.sleep(2)

        # Wait for SMS Ready
        time.sleep(3)

        # Set SMS mode
        for _ in range(3):
            resp = send_at("AT+CMGF=1", 2000)
            if "OK" in resp:
                break
            print("Retrying text mode setup...")
            time.sleep(1)

        send_at("AT+CNMI=1,2,0,0,0")  # Enable new SMS notifications
        send_at("AT+CSQ")             # Check signal strength

        print(f"\n✅ SIM800C Ready! SIM: {MY_PHONE}")
        print("Commands: 's' = Send SMS, 'c' = Make Call, 'q' = Quit")

    except Exception as e:
        print(f"Error: Cannot open {PORT} → {e}")
        sys.exit(1)


def send_sms(phone, message):
    """Send an SMS safely without thread conflicts."""
    print(f"\nSending SMS to {phone}: '{message}'")
    with lock:
        resp = send_at("AT+CMGF=1", 2000)
        if "OK" not in resp:
            print(f"Failed to set text mode! Response: {resp}")
            return False

        response = send_at(f'AT+CMGS="{phone}"', 3000)
        if ">" not in response:
            print("No '>' prompt. Cannot send SMS.")
            return False

        # Send message and Ctrl+Z
        ser.write((message + "\r").encode())
        time.sleep(0.5)
        ser.write(bytes([26]))  # Ctrl+Z
        ser.flush()
        print("Waiting for send confirmation...")

        timeout = 20
        start = time.time()
        full_resp = ""
        while time.time() - start < timeout:
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                full_resp += chunk
                if "+CMGS:" in full_resp and "OK" in full_resp:
                    print("✅ SMS SENT SUCCESSFULLY!")
                    print(f"Response: {full_resp.strip()}")
                    return True
            time.sleep(0.1)

        print("❌ SMS SEND TIMEOUT!")
        print(f"Last modem output:\n{full_resp.strip()}")
        return False


def make_call(phone):
    """Make a 20-second call."""
    print(f"\nCalling {phone}...")
    with lock:
        send_at(f"ATD{phone};", 2000)
    time.sleep(20)
    send_at("ATH", 1000)
    print("Call ended.")


def handle_incoming_sms():
    """Listen for incoming SMS and auto-reply."""
    buffer = ""
    while True:
        try:
            if ser and ser.in_waiting:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                lines = buffer.split('\n')
                buffer = lines[-1]

                for line in lines[:-1]:
                    line = line.strip()
                    if line.startswith('+CMT:'):
                        print(f"\nIncoming SMS Header: {line}")
                        parts = line.split(',')
                        if len(parts) > 1:
                            sender = parts[1].strip().strip('"')
                            body = ""
                            time.sleep(0.3)
                            while ser.in_waiting:
                                body_line = ser.readline().decode('utf-8', errors='ignore').strip()
                                if body_line and not body_line.startswith('+'):
                                    body += body_line
                                else:
                                    break
                            body = body.strip()
                            print(f"📩 From: {sender}\nMessage: '{body}'")
                            if body.lower() == "hi":
                                print("Auto-replying...")
                                send_sms(sender, AUTO_REPLY_MSG)
                    elif line and not line.startswith('OK'):
                        print(f"Modem: {line}")
        except Exception as e:
            print(f"[SMS Thread Error] {e}")
        time.sleep(0.1)


def main():
    init_modem()

    # Start SMS listener
    sms_thread = threading.Thread(target=handle_incoming_sms, daemon=True)
    sms_thread.start()

    print("\n" + "=" * 50)
    print("READY! Type commands below:")
    print("=" * 50)

    while True:
        try:
            cmd = input("\nEnter (s/c/q): ").strip().lower()
            if cmd == 'q':
                print("Goodbye!")
                if ser:
                    ser.close()
                break
            elif cmd == 's':
                phone = input(f"Phone (default {MY_PHONE}): ").strip() or MY_PHONE
                msg = input("Message: ").strip()
                if msg:
                    send_sms(phone, msg)
                else:
                    print("Empty message!")
            elif cmd == 'c':
                phone = input(f"Call (default {MY_PHONE}): ").strip() or MY_PHONE
                make_call(phone)
            else:
                print("Use: s = send, c = call, q = quit")
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

    if ser:
        ser.close()


if __name__ == "__main__":
    main()
