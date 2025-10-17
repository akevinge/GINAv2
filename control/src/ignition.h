#pragma once

// Set up ignition relay GPIO pin.
void setup_ignition_relay();

// Set ignition relay to high. This connects COM -> NO.
void set_ignition_relay_high();

// Set ignition relay to low. This connects COM -> NC.
void set_ignition_relay_low();
