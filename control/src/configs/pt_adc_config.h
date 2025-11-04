#pragma once

#include <driver/gpio.h>
#include <esp32_driver_mcp320x/mcp320x.h>
#include <hal/spi_types.h>

#include <array>
#include <cstdint>

// Shared among ADC SPI devices.
constexpr gpio_num_t ADC_SPI_MOSI = GPIO_NUM_5;
constexpr gpio_num_t ADC_SPI_MISO = GPIO_NUM_7;
constexpr gpio_num_t ADC_SPI_CLK = GPIO_NUM_19;
constexpr spi_host_device_t ADC_SPI_HOST = SPI3_HOST;
// Number of times to sample voltage when reading.
constexpr uint16_t PT_ADC_VOLTAGE_SAMPLE_COUNT = 400;
constexpr uint16_t PT_ADC_MAX_VOLTAGE_MV = 5000;  // 5V reference.
constexpr float PT_VOLTAGE_TOLERANCE =
    0.05 * PT_ADC_MAX_VOLTAGE_MV;  // 250mV tolerance for 5V ref.

// SPI configuration for an MCP3204 device.
struct MP2304SpiConfig {
  gpio_num_t cs;            // Chip select
  uint16_t ref_voltage;     // Reference voltage in mV
  uint32_t clock_speed_hz;  // Clock speed
};

// SPI configurations for each MCP3204 device.
constexpr MP2304SpiConfig MP2304_SPI_CONFIGS[] = {
    {
        .cs = GPIO_NUM_4,
        .ref_voltage = PT_ADC_MAX_VOLTAGE_MV,  // 5V
        .clock_speed_hz = 2 * 1000 * 1000,     // 2 Mhz
    },
    {
        .cs = GPIO_NUM_6,
        .ref_voltage = PT_ADC_MAX_VOLTAGE_MV,  // 5V
        .clock_speed_hz = 2 * 1000 * 1000,     // 2 Mhz
    },
};

// Map of chip select GPIO to MCP3204 handle.
static std::array<mcp320x_t*, GPIO_NUM_MAX> MP2304_HANDLES{};
