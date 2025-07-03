#include <wiringPi.h>
#include <chrono>
#include <thread>
#include <cstdint>
#include <iostream>
#include <sys/time.h>

#define RX_PIN 12           // BCM 18 = physical pin 12 (Data)
#define CLK_PIN 6          // BCM 22 = physical pin 15 (Clock)

uint8_t receiveByte() {
    uint8_t byte = 0;
    for (int i = 0; i < 8; ++i) {
        while (digitalRead(CLK_PIN) == LOW);  // Wait for clock to go high (rising edge)
        byte |= (digitalRead(RX_PIN) << i);   // Read data bit
        while (digitalRead(CLK_PIN) == HIGH); // Wait for clock to go low (falling edge)
    }
    return byte;
}

uint64_t receiveTimestamp() {
    uint64_t ts = 0;
    for (int i = 0; i < 8; ++i) {
        ts <<= 8;
        ts |= receiveByte();  // Receive timestamp byte by byte
    }
    return ts;
}

uint64_t nowNs() {
    return std::chrono::high_resolution_clock::now().time_since_epoch().count();
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: sudo ./list <correction offset in ns> (common is 0 or 900'000)\n";
        return 1;
    }

    long long corr_offset = std::stoi(argv[1]);

    wiringPiSetupGpio(); // BCM numbering
    pinMode(RX_PIN, INPUT); // Data pin
    pinMode(CLK_PIN, INPUT); // Clock pin
    pullUpDnControl(RX_PIN, PUD_UP);

    while (true) {

        while (digitalRead(CLK_PIN) == LOW);

        uint64_t localTs = nowNs();
        uint64_t recvTs = receiveTimestamp();  // Receive the timestamp
        
        int64_t offset = static_cast<int64_t>(recvTs) - static_cast<int64_t>(localTs);
        std::cout << "Received timestamp: " << recvTs << ", local: " << localTs
                  << ", offset: " << offset << " ns" << std::endl;

        // Optional: adjust time (needs root)
        uint64_t correctedTs = nowNs() + offset - corr_offset;
        struct timeval tv;
        tv.tv_sec = (correctedTs / 1'000'000'000);
        tv.tv_usec = (correctedTs % 1'000'000'000) / 1000;
        settimeofday(&tv, NULL);
    }
}
