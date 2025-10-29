#pragma once

#include <driver/gpio.h>
#include <esp32_driver_mcp320x/mcp320x.h>
#include <hal/spi_types.h>

#include <array>
#include <cstdint>

// Shared among ADC SPI devices.
constexpr gpio_num_t ADC_SPI_MOSI = GPIO_NUM_33;
constexpr gpio_num_t ADC_SPI_MISO = GPIO_NUM_34;
constexpr gpio_num_t ADC_SPI_CLK = GPIO_NUM_19;
constexpr spi_host_device_t ADC_SPI_HOST = SPI3_HOST;
// Number of times to sample voltage when reading.
constexpr uint16_t PT_ADC_VOLTAGE_SAMPLE_COUNT = 400;

struct MP2304SpiConfig {
  gpio_num_t cs;            // Chip select
  uint16_t ref_voltage;     // Reference voltage in mV
  uint32_t clock_speed_hz;  // Clock speed
};

constexpr MP2304SpiConfig MP2304_SPI_CONFIGS[] = {
    {
        .cs = GPIO_NUM_5,
        .ref_voltage = 5000,                // 5V
        .clock_speed_hz = 2 * 1000 * 1000,  // 2 Mhz
    },
    {
        .cs = GPIO_NUM_7,
        .ref_voltage = 5000,                // 5V
        .clock_speed_hz = 2 * 1000 * 1000,  // 2 Mhz
    },
};

constexpr size_t num_unqiue_adcs() {
  return sizeof(MP2304_SPI_CONFIGS) / sizeof(MP2304_SPI_CONFIGS[0]);
}

constexpr size_t MP2304_SPI_CONFIGS_LENGTH =
    sizeof(MP2304_SPI_CONFIGS) / sizeof(MP2304_SPI_CONFIGS[0]);

static std::array<mcp320x_t*, GPIO_NUM_MAX> MP2304_HANDLES{};
