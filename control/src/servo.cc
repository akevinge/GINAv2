#include "servo.h"

#include <driver/gpio.h>
#include <driver/ledc.h>
#include <esp_log.h>

#include <algorithm>
#include <array>
#include <cassert>

#include "config.h"
#include "servo_config.h"

// Next available channel that has not been mapped to a gpio.
static ledc_channel_t LEDC_CHANNEL = LEDC_CHANNEL_0;
// Map of GPIO -> channel, used to look up channel by GPIO when setting angle.
static std::array<ledc_channel_t, GPIO_NUM_MAX> GPIO_TO_CHANNEL_MAP = [] {
  std::array<ledc_channel_t, GPIO_NUM_MAX> a{};
  a.fill(LEDC_CHANNEL_MAX);
  return a;
}();

void setup_servo_pwm_timer() {
  ledc_timer_config_t ledc_timer = {
      .speed_mode = LEDC_MODE,
      .duty_resolution = LEDC_DUTY_RES,
      .timer_num = LEDC_TIMER,
      .freq_hz = LEDC_FREQUENCY,
  };
  ledc_timer_config(&ledc_timer);
}

void setup_servo_pin(gpio_num_t gpio_num) {
  // Ensure that we don't create more channels than supported
  // (i.e. if the channel is not outside of 0-LEDC_CHANNEL_MAX-1).
  assert(LEDC_CHANNEL < LEDC_CHANNEL_MAX);
  gpio_reset_pin(gpio_num);
  ledc_channel_config_t ledc_channel = {
      .gpio_num = gpio_num,
      .speed_mode = LEDC_MODE,
      .channel = LEDC_CHANNEL,
      .intr_type = LEDC_INTR_DISABLE,
      .timer_sel = LEDC_TIMER,
      .duty = 0,
  };
  ledc_channel_config(&ledc_channel);
  // Map channel to map.
  GPIO_TO_CHANNEL_MAP[gpio_num] = LEDC_CHANNEL;
  // Ensure no servos share the same PWM.
  LEDC_CHANNEL =
      static_cast<ledc_channel_t>(static_cast<int>(LEDC_CHANNEL) + 1);
}

void set_servo_angle(gpio_num_t gpio_num, int angle, int max_angle) {
  ledc_channel_t channel = GPIO_TO_CHANNEL_MAP[gpio_num];
  int pulsewidth = SERVO_MIN_PW + (SERVO_MAX_PW - SERVO_MIN_PW) *
                                      (static_cast<float>(angle) / max_angle);
  int duty_cycle = (pulsewidth * 1023) /
                   SERVO_DUTY_PERIOD;  // 1024 is 2^10 for 10-bit resolution
  ESP_LOGI("SERVO", "Angle: %d -> Pulsewidth: %lu us -> Duty: %lu", angle,
           pulsewidth, duty_cycle);
  ledc_set_duty(LEDC_MODE, channel, duty_cycle);
  ledc_update_duty(LEDC_MODE, channel);
}
