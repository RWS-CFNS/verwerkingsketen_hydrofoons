#include <wiringPi.h>
#include <chrono>
#include <iostream>
#include <sys/time.h>
#include <cstdlib>
#include <string>
#include <thread>


int64_t chosen_timestamp_us = 1'714'406'400'000'000; // + 700

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


int main() {
    // Set up GPIO pins
    wiringPiSetupGpio();
    int pulse_pin = 5;
    int pulse_pin2 = 6;
    pinMode(pulse_pin, OUTPUT);
    pinMode(pulse_pin2, OUTPUT);
    digitalWrite(pulse_pin, LOW);
    digitalWrite(pulse_pin2, LOW);

    // Feedback
    set_led_brightness(1);
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    // Start pulse and set time
    digitalWrite(pulse_pin, HIGH);
    digitalWrite(pulse_pin2, HIGH);
    set_time_from_timestamp(chosen_timestamp_us);

    // End pulse
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    digitalWrite(pulse_pin, LOW);
    digitalWrite(pulse_pin2, LOW);

    // Feedback
    set_led_brightness(0);

    return 0;
}

// g++ sender.cpp -lwiringPi -o sender
// sudo ./sender