#pragma once

#include <driver/gpio.h>

// Configures LEDC timer, used for pwm.
void setup_servo_pwm_timer();

// Sets up GPIO pin for servo and maps the pin to a channel.
void setup_servo_pin(gpio_num_t gpio_num);

// Set the angle on a given servo. `max_angle` is used to calculate
// the pulse width, because not all servos have the same max angle.
void set_servo_angle(gpio_num_t gpio_num, int angle, int max_angle);