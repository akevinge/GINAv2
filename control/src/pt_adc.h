#pragma once

#include <driver/gpio.h>
#include <esp32_driver_mcp320x/mcp320x.h>

#include <cstdint>

// Initializes the SPI bus and MCP3204 ADC devices used for pressure transducer
// readings.
void init_pt_adc_spi();

// Reads a voltage from the ADC specified by chip_select and channel.
float pt_adc_read_raw_voltage(gpio_num_t chip_select,
                              mcp320x_channel_t channel);
