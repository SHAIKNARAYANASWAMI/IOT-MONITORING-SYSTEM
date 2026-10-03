#include "sensor.h"

#include <cstdio>
#include <cstdlib>

namespace device {

namespace {
struct AlarmName {
    std::uint8_t flag;
    const char* name;
};

const AlarmName kAlarmNames[] = {
    {ALARM_HIGH_TEMP, "HIGH_TEMP"},
    {ALARM_LOW_TEMP, "LOW_TEMP"},
    {ALARM_HIGH_VOLTAGE, "HIGH_VOLTAGE"},
    {ALARM_LOW_VOLTAGE, "LOW_VOLTAGE"},
    {ALARM_HIGH_CURRENT, "HIGH_CURRENT"},
    {ALARM_LOW_BATTERY, "LOW_BATTERY"},
};

float randomBetween(float lo, float hi) {
    return lo + (hi - lo) * (static_cast<float>(std::rand()) / static_cast<float>(RAND_MAX));
}
}  // namespace

CircularBuffer::CircularBuffer() : buf_{}, head_(0), count_(0) {}

void CircularBuffer::push(float value) {
    buf_[head_] = value;
    head_ = (head_ + 1) % CAPACITY;  // wrap around: overwrites the oldest
    if (count_ < CAPACITY) {
        ++count_;
    }
}

std::size_t CircularBuffer::size() const { return count_; }

float CircularBuffer::average() const { return calculateAverage(buf_, count_); }

void readSensorData(SensorData& out, bool injectFault) {
    out.temperature = randomBetween(25.0f, 40.0f);
    out.humidity = randomBetween(40.0f, 70.0f);
    out.voltage = randomBetween(225.0f, 235.0f);
    out.current = randomBetween(2.0f, 6.0f);
    out.battery = static_cast<std::uint8_t>(randomBetween(60.0f, 100.0f));
    if (injectFault) {
        out.temperature = randomBetween(55.0f, 80.0f);
        out.battery = static_cast<std::uint8_t>(randomBetween(5.0f, 15.0f));
    }
}

bool validateSensorData(const SensorData& d) {
    // NaN fails every comparison, so "!(x >= lo && x <= hi)" rejects NaN too.
    if (!(d.temperature >= -50.0f && d.temperature <= 150.0f)) return false;
    if (!(d.humidity >= 0.0f && d.humidity <= 100.0f)) return false;
    if (!(d.voltage >= 0.0f && d.voltage <= 500.0f)) return false;
    if (!(d.current >= 0.0f && d.current <= 100.0f)) return false;
    if (d.battery > 100) return false;
    return true;
}

std::uint8_t checkThreshold(const SensorData& d, const Thresholds& t) {
    std::uint8_t flags = ALARM_NONE;
    if (d.temperature > t.tempMax) flags |= ALARM_HIGH_TEMP;     // set bit
    if (d.temperature < t.tempMin) flags |= ALARM_LOW_TEMP;
    if (d.voltage > t.voltMax) flags |= ALARM_HIGH_VOLTAGE;
    if (d.voltage < t.voltMin) flags |= ALARM_LOW_VOLTAGE;
    if (d.current > t.currentMax) flags |= ALARM_HIGH_CURRENT;
    if (d.battery < t.batteryMin) flags |= ALARM_LOW_BATTERY;
    return flags;
}

float calculateAverage(const float* values, std::size_t count) {
    if (values == nullptr || count == 0) return 0.0f;
    float sum = 0.0f;
    for (std::size_t i = 0; i < count; ++i) {
        sum += values[i];
    }
    return sum / static_cast<float>(count);
}

int generateAlert(std::uint8_t flags, char* out, std::size_t outSize) {
    if (out == nullptr || outSize == 0) return 0;
    out[0] = '\0';
    std::size_t used = 0;
    int count = 0;
    for (const AlarmName& entry : kAlarmNames) {
        if ((flags & entry.flag) == 0) continue;  // test bit
        int n = std::snprintf(out + used, outSize - used, "%s%s", count ? "," : "", entry.name);
        if (n < 0 || static_cast<std::size_t>(n) >= outSize - used) break;  // would overflow
        used += static_cast<std::size_t>(n);
        ++count;
    }
    return count;
}

int countAlarms(std::uint8_t flags) {
    int count = 0;
    while (flags) {
        flags &= static_cast<std::uint8_t>(flags - 1);  // clear lowest set bit
        ++count;
    }
    return count;
}

}  // namespace device