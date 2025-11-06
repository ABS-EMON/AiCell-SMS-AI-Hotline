import serial
import time
import sys

PORT = 'COM3'
BAUD_RATE = 115200


def init_modem():
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        return ser
    except Exception as e:
        print(f"Error: {e}")
        return None


def send_at(ser, command, timeout=2):
    """Send AT command and return response"""
    print(f"> {command}")
    ser.write((command + '\r\n').encode())
    time.sleep(timeout)

    response = ""
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    response = response.strip()
    if response:
        print(f"< {response}")
    return response


def network_troubleshoot(ser):
    """Comprehensive network troubleshooting"""
    print("\n" + "=" * 60)
    print("NETWORK TROUBLESHOOTING")
    print("=" * 60)

    # 1. Check basic modem functionality
    print("1. Basic modem check...")
    response = send_at(ser, "AT")
    if "OK" not in response:
        print("✗ Modem not responding")
        return False
    print("✓ Modem responding")

    # 2. Check SIM card
    print("\n2. SIM card check...")
    response = send_at(ser, "AT+CPIN?")
    if "READY" in response:
        print("✓ SIM card is ready")
    else:
        print("✗ SIM card issue:", response)
        return False

    # 3. Check radio functionality
    print("\n3. Radio functionality...")
    response = send_at(ser, "AT+CFUN?")
    if "+CFUN: 1" in response:
        print("✓ Full functionality mode")
    else:
        print("⚠ Radio may be off, trying to enable...")
        send_at(ser, "AT+CFUN=1", 5)

    # 4. Check signal strength
    print("\n4. Signal strength...")
    response = send_at(ser, "AT+CSQ")
    if "+CSQ:" in response:
        try:
            # Extract signal quality
            csq_part = response.split("+CSQ:")[1].split(",")[0].strip()
            signal = int(csq_part)
            if signal == 0:
                print("✗ NO SIGNAL (0) - Check antenna!")
            elif signal <= 10:
                print(f"⚠ VERY WEAK signal ({signal})")
            elif signal <= 20:
                print(f"⚠ WEAK signal ({signal})")
            else:
                print(f"✓ Good signal ({signal})")
        except:
            print(f"Signal reading: {response}")
    else:
        print("✗ Cannot read signal")

    # 5. Check network registration
    print("\n5. Network registration...")
    response = send_at(ser, "AT+CREG?")
    if "+CREG:" in response:
        try:
            status = response.split(",")[1].strip()
            status_codes = {
                "0": "Not registered",
                "1": "Registered (home)",
                "2": "Searching...",
                "3": "Registration denied",
                "4": "Unknown",
                "5": "Registered (roaming)"
            }
            print(f"Status: {status_codes.get(status, status)}")
        except:
            print(f"Registration: {response}")
    else:
        print("✗ Cannot read registration")

    # 6. Check available networks
    print("\n6. Searching for networks...")
    send_at(ser, "AT+COPS=?", 10)  # List available networks

    # 7. Manual network selection
    print("\n7. Trying manual network registration...")
    response = send_at(ser, "AT+COPS=0", 10)  # Auto selection
    if "OK" in response:
        print("✓ Network auto-select command sent")

    print("\n" + "=" * 60)
    return True


def force_network_registration(ser):
    """Try to force network registration"""
    print("\n🔄 FORCING NETWORK REGISTRATION...")

    # Method 1: Reset radio
    print("1. Resetting radio...")
    send_at(ser, "AT+CFUN=0", 5)  # Turn off
    send_at(ser, "AT+CFUN=1", 10)  # Turn on

    # Method 2: Manual network search
    print("2. Manual network search...")
    send_at(ser, "AT+COPS=?", 15)  # Search networks

    # Method 3: Auto register
    print("3. Auto registration...")
    send_at(ser, "AT+COPS=0", 15)

    # Wait and check
    print("4. Waiting for registration...")
    for i in range(30):  # Wait 30 seconds
        response = send_at(ser, "AT+CREG?")
        if "+CREG:" in response:
            if ",1" in response or ",5" in response:
                print("✓ NETWORK REGISTERED SUCCESSFULLY!")
                return True
        print(f"   Still searching... {29 - i}s remaining")
        time.sleep(1)

    print("✗ Network registration failed")
    return False


def send_sms_anyway(ser, phone, message):
    """Try to send SMS even without network (for testing)"""
    print(f"\n📨 ATTEMPTING SMS (Network status ignored)")
    print(f"To: {phone}")
    print(f"Message: '{message}'")

    # Set text mode
    send_at(ser, "AT+CMGF=1")

    # Try to send SMS
    print(f"> AT+CMGS=\"{phone}\"")
    ser.write(f'AT+CMGS="{phone}"\r\n'.encode())

    # Wait for prompt
    timeout = 15
    start_time = time.time()

    while time.time() - start_time < timeout:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"Response: {repr(data)}")
            if ">" in data:
                print("✓ Got prompt, sending message...")
                # Send message
                ser.write(message.encode())
                time.sleep(1)
                ser.write(bytes([26]))  # Ctrl+Z
                print("Sent message + Ctrl+Z")

                # Wait for any response
                time.sleep(10)
                final_response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"Final: {repr(final_response)}")

                if "+CMGS:" in final_response:
                    print("🎉 SMS SENT! (Queued by network)")
                    return True
                else:
                    print("⚠ SMS may be queued or failed")
                    return False
        time.sleep(0.5)

    print("✗ No prompt received")
    return False


def main():
    print("SIM800C NETWORK TROUBLESHOOTER")

    ser = init_modem()
    if not ser:
        return

    try:
        # Step 1: Troubleshoot network
        network_troubleshoot(ser)

        # Step 2: Try to force registration
        if not force_network_registration(ser):
            print("\n❌ CANNOT CONNECT TO NETWORK")
            print("\nTROUBLESHOOTING STEPS:")
            print("1. ✅ Check antenna connection")
            print("2. ✅ Ensure SIM card is inserted properly")
            print("3. ✅ Move module to better location (near window)")
            print("4. ✅ Wait 2-3 minutes after power on")
            print("5. ⚠ Check if SIM has active service")
            print("6. ⚠ Try different SIM card if possible")

            # Try SMS anyway
            choice = input("\nTry sending SMS anyway? (y/n): ").lower()
            if choice == 'y':
                phone = input("Phone: ").strip() or "+8801644110760"
                message = input("Message: ").strip() or "Test from SIM800C"
                send_sms_anyway(ser, phone, message)

    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ser.close()
        print("\nConnection closed")


if __name__ == "__main__":
    main()