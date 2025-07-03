#include <wiringPi.h>
#include <thread>       // for std::this_thread::sleep_for
#include <chrono>       // for std::chrono::milliseconds/seconds

#define RELAY_GPIO 26  // BCM GPIO17 (physical pin 11)

int main() {
    if (wiringPiSetupGpio() == -1) {
        return 1;
    }

    pinMode(RELAY_GPIO, OUTPUT);
    digitalWrite(RELAY_GPIO, LOW);

    // Wait 1 second before triggering
    std::this_thread::sleep_for(std::chrono::seconds(1));

    // Trigger 5 ms pulse
    digitalWrite(RELAY_GPIO, HIGH);
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
    digitalWrite(RELAY_GPIO, LOW);

    return 0;
}
