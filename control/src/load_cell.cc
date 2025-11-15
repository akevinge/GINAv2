#include "load_cell.h"

#include <esp_err.h>
#include <hx711.h>

#include <cstdint>

#include "configs/load_cell_config.h"

hx711_t dev = {
    .dout = HX711_DOUT_GPIO_NUM,
    .pd_sck = HX711_PD_SCK_GPIO_NUM,
    .gain = HX711_GAIN,
};

void init_load_cell() { ESP_ERROR_CHECK(hx711_init(&dev)); }

esp_err_t read_raw_load_cell(int32_t* value) {
  esp_err_t r = hx711_wait(&dev, HX711_MAX_TIMEOUT_MS);
  if (r != ESP_OK) {
    return r;
  }

  r = hx711_read_average(&dev, HX711_AVG_SAMPLE_COUNT, value);
  if (r != ESP_OK) {
    return r;
  }

  return ESP_OK;
}