#pragma once

#include <driver/gpio.h>

void setup_servo_pwm_timer();

void setup_servo_pin(gpio_num_t gpio_num);

void set_servo_angle(gpio_num_t gpio_num, int angle, int max_angle);