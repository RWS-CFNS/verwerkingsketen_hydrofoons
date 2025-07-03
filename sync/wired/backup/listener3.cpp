#include <gpiod.h>
#include <chrono>
#include <iostream>
#include <atomic>
#include <thread>
#include <ctime>
#include <cstdlib>

constexpr const char* CHIPNAME = "gpiochip0";  // Usually correct for Raspberry Pi
constexpr int LINE_NUM = 6;                    // BCM pin number (e.g., GPIO6)
int64_t chosen_timestamp_ns = 1'714'406'400'000'000'000;

std::atomic<bool> received(false);

void set_time_from_timestamp_ns(int64_t target_ns) {
    struct timespec ts;
    ts.tv_sec = target_ns / 1'000'000'000;
    ts.tv_nsec = target_ns % 1'000'000'000;

    if (clock_settime(CLOCK_REALTIME, &ts) == 0) {
        std::cout << "System time set to " << ts.tv_sec << " s and " << ts.tv_nsec << " ns.\n";
    } else {
        perror("clock_settime");
    }
}

void set_led_brightness(int value) {
    std::string cmd = "sudo sh -c \"echo " + std::to_string(value) + " > /sys/class/leds/ACT/brightness\"";
    system(cmd.c_str());
}

int main() {
    gpiod_chip* chip = gpiod_chip_open_by_name(CHIPNAME);
    if (!chip) {
        std::cerr << "Failed to open GPIO chip\n";
        return 1;
    }

    gpiod_line* line = gpiod_chip_get_line(chip, LINE_NUM);
    if (!line) {
        std::cerr << "Failed to get GPIO line\n";
        gpiod_chip_close(chip);
        return 1;
    }

    if (gpiod_line_request_rising_edge_events(line, "time_sync_listener") < 0) {
        std::cerr << "Failed to request rising edge events\n";
        gpiod_chip_close(chip);
        return 1;
    }

    // Feedback LED ON
    set_led_brightness(1);
    std::cout << "Listening for rising edge on GPIO" << LINE_NUM << "...\n";

    while (!received) {
        struct gpiod_line_event event;
        int ret = gpiod_line_event_wait(line, nullptr);  // Blocks until event
        if (ret < 0) {
            std::cerr << "Error waiting for event\n";
            break;
        } else if (ret > 0) {
            if (gpiod_line_event_read(line, &event) == 0 && event.event_type == GPIOD_LINE_EVENT_RISING_EDGE) {
                set_time_from_timestamp_ns(chosen_timestamp_ns);
                received = true;
            }
        }
    }

    // Cleanup
    set_led_brightness(0);
    gpiod_line_release(line);
    gpiod_chip_close(chip);
    return 0;
}

// sudo apt install libgpiod-dev
// g++ listener3.cpp -lgpiod -o listener3
// sudo ./listener