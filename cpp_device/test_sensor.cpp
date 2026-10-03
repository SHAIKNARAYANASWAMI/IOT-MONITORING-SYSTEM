#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <limits>

#include "sensor.h"

using namespace device;

static const Thresholds kLimits = {5.0f, 50.0f, 200.0f, 250.0f, 10.0f, 20};

static SensorData normal() { return SensorData{30.0f, 50.0f, 230.0f, 4.0f, 80}; }

static void test_normal_reading_has_no_alarms() {
    assert(checkThreshold(normal(), kLimits) == ALARM_NONE);
}

static void test_high_temperature_sets_only_that_bit() {
    SensorData d = normal();
    d.temperature = 62.0f;
    assert(checkThreshold(d, kLimits) == ALARM_HIGH_TEMP);
}

static void test_multiple_alarms_combine_bits() {
    SensorData d = normal();
    d.temperature = 62.0f;
    d.battery = 7;
    std::uint8_t flags = checkThreshold(d, kLimits);
    assert(flags == (ALARM_HIGH_TEMP | ALARM_LOW_BATTERY));
    assert(flags == 0x21);
    assert(countAlarms(flags) == 2);
}

static void test_value_at_limit_is_not_alarm() {
    SensorData d = normal();
    d.temperature = 50.0f;
    assert(checkThreshold(d, kLimits) == ALARM_NONE);
}

static void test_validate_accepts_normal() {
    assert(validateSensorData(normal()));
}

static void test_validate_rejects_out_of_range() {
    SensorData d = normal();
    d.temperature = 9999.0f;
    assert(!validateSensorData(d));
    d = normal();
    d.battery = 101;
    assert(!validateSensorData(d));
}

static void test_validate_rejects_nan() {
    SensorData d = normal();
    d.humidity = std::numeric_limits<float>::quiet_NaN();
    assert(!validateSensorData(d));
}

static void test_calculate_average() {
    const float v[] = {10.0f, 20.0f, 30.0f};
    assert(std::fabs(calculateAverage(v, 3) - 20.0f) < 1e-5f);
    assert(calculateAverage(nullptr, 3) == 0.0f);
    assert(calculateAverage(v, 0) == 0.0f);
}

static void test_circular_buffer_overwrites_oldest() {
    CircularBuffer cb;
    for (int i = 1; i <= 7; ++i) cb.push(static_cast<float>(i));
    assert(cb.size() == CircularBuffer::CAPACITY);
    // window holds 3,4,5,6,7 -> average 5
    assert(std::fabs(cb.average() - 5.0f) < 1e-5f);
}

static void test_generate_alert_text() {
    char buf[96];
    int n = generateAlert(ALARM_HIGH_TEMP | ALARM_LOW_BATTERY, buf, sizeof(buf));
    assert(n == 2);
    assert(std::string(buf) == "HIGH_TEMP,LOW_BATTERY");
}

static void test_generate_alert_never_overflows_small_buffer() {
    char buf[8];
    generateAlert(0x3F, buf, sizeof(buf));
    assert(std::strlen(buf) < sizeof(buf));
}

static void test_count_alarms() {
    assert(countAlarms(0) == 0);
    assert(countAlarms(0x3F) == 6);
    assert(countAlarms(0x21) == 2);
}

int main() {
    test_normal_reading_has_no_alarms();
    test_high_temperature_sets_only_that_bit();
    test_multiple_alarms_combine_bits();
    test_value_at_limit_is_not_alarm();
    test_validate_accepts_normal();
    test_validate_rejects_out_of_range();
    test_validate_rejects_nan();
    test_calculate_average();
    test_circular_buffer_overwrites_oldest();
    test_generate_alert_text();
    test_generate_alert_never_overflows_small_buffer();
    test_count_alarms();
    std::printf("All 12 C++ tests passed\n");
    return 0;
}