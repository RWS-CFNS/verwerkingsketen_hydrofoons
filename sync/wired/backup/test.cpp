#include <wiringPi.h>
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    // Use BCM numbering
    if (wiringPiSetupGpio() == -1) {
        std::cerr << "Failed to set up GPIO\n";
        return 1;
    }

    int pulse_pin = 5;   // BCM 5
    int pulse_pin2 = 6;  // BCM 6

    pinMode(pulse_pin, OUTPUT);
    pinMode(pulse_pin2, OUTPUT);

    digitalWrite(pulse_pin, LOW);
    digitalWrite(pulse_pin2, LOW);

    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    std::cout << "Starting pulse and measuring delay between digitalWrite calls...\n";

    auto t1 = std::chrono::high_resolution_clock::now();
    digitalWrite(pulse_pin, HIGH);
    auto t2 = std::chrono::high_resolution_clock::now();
    digitalWrite(pulse_pin2, HIGH);
    auto t3 = std::chrono::high_resolution_clock::now();

    auto dt1 = std::chrono::duration_cast<std::chrono::microseconds>(t2 - t1).count();
    auto dt2 = std::chrono::duration_cast<std::chrono::microseconds>(t3 - t2).count();
    auto dt_total = std::chrono::duration_cast<std::chrono::microseconds>(t3 - t1).count();

    std::cout << "---------------------------------------------\n";
    std::cout << "Time from first write START to first write END: " << dt1 << " µs\n";
    std::cout << "Time between pin1 HIGH and pin2 HIGH:           " << dt2 << " µs\n";
    std::cout << "Total time for both digitalWrite calls:         " << dt_total << " µs\n";
    std::cout << "---------------------------------------------\n";

    // Leave pins HIGH for 10 ms
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    digitalWrite(pulse_pin, LOW);
    digitalWrite(pulse_pin2, LOW);

    return 0;
}
