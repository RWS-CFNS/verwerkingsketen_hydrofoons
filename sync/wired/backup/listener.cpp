#include <wiringPi.h>
#include <chrono>
#include <iostream>
#include <sys/time.h>
#include <cstdlib>
#include <string>
#include <thread>
#include <atomic>

int64_t chosen_timestamp_us = 1'714'406'400'000'000;

void set_time_from_timestamp(int64_t target_us) {
    struct timeval tv;
    tv.tv_sec = target_us / 1'000'000;
    tv.tv_usec = target_us % 1'000'000;
    if (settimeofday(&tv, nullptr) == 0) {
        std::cout << "System time set to " << tv.tv_sec << " s and " << tv.tv_usec << " us.\n";
    } else {
        perror("settimeofday");
    }
}

void set_led_brightness(int value) {
    std::string cmd = "sudo sh -c \"echo " + std::to_string(value) + " > /sys/class/leds/ACT/brightness\"";
    system(cmd.c_str());
}

std::atomic<bool> received(false);

void on_pulse() {
    if (received) return;
    set_time_from_timestamp(chosen_timestamp_us);
    received = true;
}

int main() {
    // Set up GPIO pins
    wiringPiSetupGpio();
    int pin = 6;
    pinMode(pin, INPUT);
    wiringPiISR(pin, INT_EDGE_RISING, &on_pulse);

    // Feedback
    set_led_brightness(1);

    std::cout << "Listening for pulse...\n";
    while (!received) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    // Feedback
    set_led_brightness(0);
    return 0;
}

// g++ listener.cpp -lwiringPi -o listener
// sudo ./listener