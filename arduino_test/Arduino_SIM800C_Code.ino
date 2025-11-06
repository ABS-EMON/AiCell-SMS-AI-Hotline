#include <SoftwareSerial.h>

SoftwareSerial mySerial(2, 3);
int timeout;
void setup(){
  Serial.begin(9600);
  mySerial.begin(9600);
  Serial.println("Type\n s) to send an SMS\n r) to receive an SMS\n c) to make a call");
  Serial.println("Initializing..."); 
  delay(1000);
  mySerial.println("AT");
}

void loop(){
  if (Serial.available() > 0){
    switch (Serial.read()){
      case 's':
        SendMessage();
        break;
      case 'r':
        RecieveMessage();
        break;
      case 'c':
        CallNumber();
        break;
    }
 }
  if (mySerial.available()) {
    delay(1000);
    Serial.println(mySerial.readString());
  }
}

String readSerial(){
  delay(100);
  if (mySerial.available()) {
    return mySerial.readString();
  }
}

void CallNumber() {
  mySerial.println("ATD+ +94760597376;");
  Serial.println(readSerial());
  delay(20000); 
  mySerial.println("ATH"); 
  delay(200);
  Serial.println(readSerial());
}
void SendMessage(){
  mySerial.println("AT+CMGF=1"); 
  Serial.println(readSerial());
  mySerial.println("AT+CMGS=\"+94760597376\"");
  Serial.println(readSerial());
  mySerial.println("Hi this is veron");
  mySerial.println((char)26);
  Serial.println(readSerial());
}

void RecieveMessage(){
  Serial.println ("SIM800C Read an SMS");
  mySerial.println("AT+CMGF=1");
  Serial.println(readSerial());
  mySerial.println("AT+CNMI=1,2,0,0,0"); 
  Serial.println(readSerial());
}
