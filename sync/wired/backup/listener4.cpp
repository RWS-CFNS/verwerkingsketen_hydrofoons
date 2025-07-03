#include <string>
#include <cstdlib>
#include <atomic>
#include <chrono>
#include <fstream>
#include <wiringPi.h>
#include <thread>
#include <iostream>

void set_led_brightness(int value) {
    std::string cmd = "sudo sh -c \"echo " + std::to_string(value) + " > /sys/class/leds/ACT/brightness\"";
    system(cmd.c_str());
}

std::atomic<bool> received(false);
long long t1 = 0;

void on_pulse() {
    auto pulse_timestamp = std::chrono::high_resolution_clock::now();
    
    if (received) return;
    
    std::ofstream file("./pulse_timestamp.txt");
    file << pulse_timestamp.time_since_epoch().count() << std::endl;
    file.close();

    received = true;
    // std::cout << "on_pulse() called << " << pulse_timestamp.time_since_epoch().count() / 1000000 << " ms\n";

    t1 = pulse_timestamp.time_since_epoch().count();
}

int main() {
    // Set up GPIO pins
    wiringPiSetupGpio();
    int input_pulse_pin = 12;
    pinMode(input_pulse_pin, INPUT);
    // wiringPiISR(input_pulse_pin, INT_EDGE_RISING, &on_pulse);

    // Feedback
    set_led_brightness(1);

    // Wait for pulse and ISR to finish
    std::cout << "Listening for pulse...\n";
    // wait while pin is low
    while (digitalRead(input_pulse_pin) == LOW) {
        // std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    on_pulse();
    // auto time1 = std::chrono::high_resolution_clock::now().time_since_epoch().count();

    // Feedback
    set_led_brightness(0);

    auto time2 = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    system("rm -f recordings/* && ./rec");
    auto time3 = std::chrono::high_resolution_clock::now().time_since_epoch().count();

    // Feedback
    set_led_brightness(1);
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    set_led_brightness(0);

    std::cout << "Time taken at start of record: " << (time2 - t1) / 1000000 << " ms\n";
    std::cout << "Time taken at end of record  : " << (time3 - t1) / 1000000 << " ms\n";

    return 0;
}

// g++ listener.cpp -lwiringPi -o listener
// sudo ./listener