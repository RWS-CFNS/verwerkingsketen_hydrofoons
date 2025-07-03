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

    t1 = pulse_timestamp.time_since_epoch().count();

    // auto now = std::chrono::high_resolution_clock::now();
    // auto now2 = now.time_since_epoch().count();
    // auto pulse2 = pulse_timestamp.time_since_epoch().count();    
    // std::cout << "on_pulse() took " << (now2 - pulse2) / 1000000 << " ms\n";
}

int pulse_pin = 5;
int pulse_pin2 = 6;
int pulse_pin3 = 13;

void set_rising_edge() {
    digitalWrite(pulse_pin, HIGH);
    digitalWrite(pulse_pin2, HIGH);
    digitalWrite(pulse_pin3, HIGH);
}

int main() {
    // Set up GPIO pins
    wiringPiSetupGpio();
    
    pinMode(pulse_pin, OUTPUT);
    pinMode(pulse_pin2, OUTPUT);
    pinMode(pulse_pin3, OUTPUT);
    
    digitalWrite(pulse_pin, LOW);
    digitalWrite(pulse_pin2, LOW);
    digitalWrite(pulse_pin3, LOW);

    // int input_pulse_pin = 12;
    // pinMode(input_pulse_pin, INPUT);
    // wiringPiISR(input_pulse_pin, INT_EDGE_RISING, &on_pulse);

    // Feedback
    set_led_brightness(1);
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    // Start pulse and set time
    // auto time1 = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    set_rising_edge();
    on_pulse();

    // End pulse after a while
    // std::this_thread::sleep_for(std::chrono::milliseconds(10));
    

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
    // std::cout << "Time at start of recording: " << time2 / 1000000 << " ms\n";

    digitalWrite(pulse_pin, LOW);
    digitalWrite(pulse_pin2, LOW);
    digitalWrite(pulse_pin3, LOW);

    return 0;
}

// g++ sender.cpp -lwiringPi -o sender
// sudo ./sender