#include <wiringPi.h>
#include <chrono>
#include <thread>
#include <cstdint>
#include <iostream>

#define TX_PIN 12           // BCM 18 = physical pin 12 (Data)
#define CLK_PIN 6          // BCM 27 = physical pin 13 (Clock)
#define BIT_DELAY_US 5'000  // 

void sendByte(uint8_t byte) {
    for (int i = 0; i < 8; ++i) {
        digitalWrite(TX_PIN, (byte >> i) & 1);  // Set data bit
        delayMicroseconds(BIT_DELAY_US);        // Wait for clock
        digitalWrite(CLK_PIN, HIGH);            // Pulse clock high
        delayMicroseconds(BIT_DELAY_US);        // Wait for clock period
        digitalWrite(CLK_PIN, LOW);             // Clock low
    }
}

void sendTimestamp(uint64_t ts) {
    for (int i = 0; i < 8; ++i) {
        sendByte((ts >> (56 - i * 8)) & 0xFF);  // Send timestamp byte by byte
    }
}

uint64_t nowNs() {
    return std::chrono::high_resolution_clock::now().time_since_epoch().count();
}

int main() {
    wiringPiSetupGpio(); // Use BCM numbering
    pinMode(TX_PIN, OUTPUT); // Data pin
    pinMode(CLK_PIN, OUTPUT); // Clock pin
    digitalWrite(TX_PIN, HIGH);  // Idle HIGH
    digitalWrite(CLK_PIN, LOW);  // Idle LOW

    while (true) {
        uint64_t t = nowNs();
        sendTimestamp(t);  // Send timestamp
        std::cout << "Sent: " << t << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1)); // Wait for 1 second before sending next timestamp
    }
}
