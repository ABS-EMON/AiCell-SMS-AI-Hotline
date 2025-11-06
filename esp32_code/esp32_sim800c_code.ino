/*
 *  ESP32 + SIM800C GSM Module
 *  ----------------------------------------
 *  CONNECTIONS:
 *  ESP32 (3.3V logic)  →  SIM800C (use logic level converter if needed)
 *
 *  ESP32 GPIO17 (TX2) → SIM800C RX
 *  ESP32 GPIO16 (RX2) → SIM800C TX
 *  GND  →  GND
 *  5V   →  SIM800C VCC (module power supply)
 *  Note: Some SIM800C modules require a separate 4V–4.2V supply.
 *
 *  Baud Rate: 9600
 */

#define RX_PIN 16  // ESP32 RX2 → SIM800C TX
#define TX_PIN 17  // ESP32 TX2 → SIM800C RX

HardwareSerial sim800(2);  // Use UART2 for SIM800C

void setup() {
  Serial.begin(115200);         // Serial Monitor
  sim800.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN); // SIM800C Serial
  
  Serial.println("ESP32 + SIM800C Communication Started");
  Serial.println("Type:");
  Serial.println(" s) Send SMS");
  Serial.println(" r) Receive SMS");
  Serial.println(" c) Call number");
  
  delay(1000);
  sim800.println("AT");
  delay(500);
  Serial.println(readSIM800());
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case 's':
        sendMessage();
        break;
      case 'r':
        receiveMessage();
        break;
      case 'c':
        callNumber();
        break;
    }
  }

  if (sim800.available()) {
    Serial.write(sim800.read());
  }
}

String readSIM800() {
  delay(500);
  String response = "";
  while (sim800.available()) {
    response += (char)sim800.read();
  }
  return response;
}

void callNumber() {
  Serial.println("Dialing...");
  sim800.println("ATD+94760597376;");  // Replace with your number
  delay(20000);                        // Wait for call duration
  sim800.println("ATH");               // Hang up
  Serial.println(readSIM800());
}

void sendMessage() {
  Serial.println("Sending SMS...");
  sim800.println("AT+CMGF=1"); // Set SMS text mode
  delay(1000);
  sim800.println("AT+CMGS=\"+94760597376\""); // Replace with your number
  delay(1000);
  sim800.println("Hi, this is Emon from ESP32 + SIM800C");
  sim800.write(26); // Ctrl+Z to send
  delay(3000);
  Serial.println(readSIM800());
}

void receiveMessage() {
  Serial.println("Reading SMS...");
  sim800.println("AT+CMGF=1"); // Set SMS text mode
  delay(1000);
  sim800.println("AT+CNMI=1,2,0,0,0"); // New message indications
  delay(1000);
  Serial.println(readSIM800());
}
