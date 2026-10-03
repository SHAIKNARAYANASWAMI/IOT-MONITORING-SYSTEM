#pragma once
#include <cstddef>
#include <cstdint>

namespace device {

// Plain data structure: one snapshot of sensor values.
// uint8_t (1 byte) for battery because it only needs 0 to 100.
struct SensorData {
    float temperature;
    float humidity;
    float voltage;
    float current;
    std::uint8_t battery;
};

struct Thresholds {
    float tempMin, tempMax;
    float voltMin, voltMax;
    float currentMax;
    std::uint8_t batteryMin;
};

// Each alarm is ONE BIT in a single byte, so 6 alarms fit in 1 byte.
enum AlarmFlag : std::uint8_t {
    ALARM_NONE         = 0,
    ALARM_HIGH_TEMP    = 1 << 0,
    ALARM_LOW_TEMP     = 1 << 1,
    ALARM_HIGH_VOLTAGE = 1 << 2,
    ALARM_LOW_VOLTAGE  = 1 << 3,
    ALARM_HIGH_CURRENT = 1 << 4,
    ALARM_LOW_BATTERY  = 1 << 5
};

// Fixed-size circular buffer. No dynamic memory (no new/malloc),
// like embedded code where heap use is avoided.
class CircularBuffer {
public:
    static const std::size_t CAPACITY = 5;

    CircularBuffer();
    void push(float value);
    std::size_t size() const;
    float average() const;

private:
    float buf_[CAPACITY];
    std::size_t head_;   // next slot to write
    std::size_t count_;  // how many slots are filled
};

// Simulated sensor read (random numbers, NOT real hardware).
// Takes a reference so the function fills the caller's struct, no copy.
void readSensorData(SensorData& out, bool injectFault);

// true if every value is physically plausible.
bool validateSensorData(const SensorData& data);

// Returns a bitmask of all alarms that are active.
std::uint8_t checkThreshold(const SensorData& data, const Thresholds& limits);

// Average of `count` floats. Pointer + length, like a C array.
float calculateAverage(const float* values, std::size_t count);

// Writes alarm names like "HIGH_TEMP,LOW_BATTERY" into a caller-owned buffer.
// Returns how many alarms were written.
int generateAlert(std::uint8_t flags, char* out, std::size_t outSize);

// Counts set bits (Kernighan's trick: each step clears the lowest set bit).
int countAlarms(std::uint8_t flags);

}  // namespace device