#include <cstdio>
#include <cstdlib>
#include <ctime>

#include "sensor.h"

int main() {
    std::srand(static_cast<unsigned>(std::time(nullptr)));

    const device::Thresholds limits = {5.0f, 50.0f, 200.0f, 250.0f, 10.0f, 20};
    device::CircularBuffer tempWindow;

    for (int i = 1; i <= 8; ++i) {
        device::SensorData data;
        bool fault = (i % 4 == 0);  // every 4th reading is faulty
        device::readSensorData(data, fault);

        if (!device::validateSensorData(data)) {
            std::printf("#%d INVALID reading, skipped\n", i);
            continue;
        }

        tempWindow.push(data.temperature);
        std::uint8_t flags = device::checkThreshold(data, limits);

        char alert[96];
        device::generateAlert(flags, alert, sizeof(alert));

        std::printf("#%d temp=%.1f avg5=%.1f battery=%u flags=0x%02X alarms=%d %s\n",
                    i, data.temperature, tempWindow.average(),
                    static_cast<unsigned>(data.battery), static_cast<unsigned>(flags),
                    device::countAlarms(flags), alert);
    }
    return 0;
}