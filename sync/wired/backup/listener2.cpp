#include <gpiod.h>
#include <sys/time.h>
#include <iostream>
#include <cstdlib>

constexpr int64_t target_us = 1714406400000000;
constexpr const char* chipname = "gpiochip0";
constexpr int pin = 6;

void set_time(int64_t us) {
    timeval tv{.tv_sec = us / 1'000'000, .tv_usec = us % 1'000'000};
    if (settimeofday(&tv, nullptr) == 0)
        std::cout << "System time set.\n";
    else
        perror("settimeofday");
}

void led(int v) {
    std::string cmd = "sudo sh -c \"echo " + std::to_string(v) + " > /sys/class/leds/ACT/brightness\"";
    system(cmd.c_str());
}

int main() {
    gpiod_chip* chip = gpiod_chip_open_by_name(chipname);
    gpiod_line* line = gpiod_chip_get_line(chip, pin);
    gpiod_line_request_rising_edge_events(line, "pulse-setter");

    led(1);
    std::cout << "Waiting for pulse on GPIO" << pin << "...\n";

    gpiod_line_event ev;
    gpiod_line_event_wait(line, nullptr);
    gpiod_line_event_read(line, &ev);
    set_time(target_us);

    led(0);
    gpiod_line_release(line);
    gpiod_chip_close(chip);
}

// sudo apt install libgpiod-dev
// g++ listener2.cpp -lgpiod -o listener2
// sudo ./listener2