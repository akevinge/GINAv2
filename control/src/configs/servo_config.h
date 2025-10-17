#pragma once

// Low speed mode is the only mode available for Heltec v3 (ESP32-S3)
#define LEDC_MODE LEDC_LOW_SPEED_MODE
// All share the same timer.
#define LEDC_TIMER LEDC_TIMER_0
// 10-bit resolution (0-1023)
#define LEDC_DUTY_RES LEDC_TIMER_10_BIT
// The frequency rate for DSSERVO DS3225MG 25KG servo is 50-330Hz PWM frequency.
// This was tested up to 600Hz on the, which still worked.
#define LEDC_FREQUENCY 330

// Min pulse width in microseconds
#define SERVO_MIN_PW 500
// Max pulse width in microseconds
#define SERVO_MAX_PW 2500
// Duty period in microseconds
constexpr float SERVO_DUTY_PERIOD = (1.0f / LEDC_FREQUENCY) * 1e6;