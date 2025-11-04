#include "pt_adc.h"

#include <driver/gpio.h>
#include <driver/spi_master.h>
#include <esp32_driver_mcp320x/mcp320x.h>

#include <array>
#include <cstdint>
#include <string>

#include "configs/pt_adc_config.h"

void init_pt_adc_spi() {
  spi_bus_config_t bus_cfg = {
      .mosi_io_num = ADC_SPI_MOSI,
      .miso_io_num = ADC_SPI_MISO,
      .sclk_io_num = ADC_SPI_CLK,
      .quadwp_io_num = GPIO_NUM_NC,
      .quadhd_io_num = GPIO_NUM_NC,
      .data4_io_num = GPIO_NUM_NC,
      .data5_io_num = GPIO_NUM_NC,
      .data6_io_num = GPIO_NUM_NC,
      .data7_io_num = GPIO_NUM_NC,
      .max_transfer_sz = 3,  // 24 bits.
      .flags = SPICOMMON_BUSFLAG_MASTER,
      .isr_cpu_id = ESP_INTR_CPU_AFFINITY_AUTO,
      .intr_flags = ESP_INTR_FLAG_LEVEL3,
  };
  spi_bus_initialize(ADC_SPI_HOST, &bus_cfg, 0);

  for (const MP2304SpiConfig& spi_config : MP2304_SPI_CONFIGS) {
    mcp320x_config_t mcp320x_cfg = {
        .host = ADC_SPI_HOST,
        .cs_io_num = spi_config.cs,
        .device_model = MCP3204_MODEL,
        .clock_speed_hz = spi_config.clock_speed_hz,
        .reference_voltage = spi_config.ref_voltage,
    };
    MP2304_HANDLES[spi_config.cs] = mcp320x_install(&mcp320x_cfg);
  }
}

float pt_adc_read_raw_voltage(gpio_num_t chip_select,
                              mcp320x_channel_t channel) {
  mcp320x_t* handle = MP2304_HANDLES[chip_select];
  assert(handle != nullptr &&
         "Attempting to read from ADC without initializing first");

  // Occupy the SPI bus for multiple transactions.
  mcp320x_acquire(handle, portMAX_DELAY);

  // Sampled voltages are returned in mV.
  uint16_t voltage_mv = 0;
  mcp320x_sample_voltage(handle, channel, MCP320X_READ_MODE_SINGLE,
                         PT_ADC_VOLTAGE_SAMPLE_COUNT, &voltage_mv);

  // Unoccupy the SPI bus.
  mcp320x_release(handle);

  // Return voltage in V.
  return voltage_mv / 1000.0f;
}
