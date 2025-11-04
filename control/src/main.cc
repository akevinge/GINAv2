#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "ignition.h"
#include "pt.h"
#include "pt_adc.h"
#include "valve.h"
#include "lora.h"

extern "C" void app_main() {
  // LoRaInit();

  // setup_ignition_relay();
  // set_ignition_relay_high();
  // vTaskDelay(pdMS_TO_TICKS(10000));  // Wait 10s
  // set_ignition_relay_low();

  // setup_valves();

  // open_valve(Valve::kOxRelease);
  // open_valve(Valve::kOxN2Purge);
  // open_valve(Valve::kFuelRelease);

  // vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second

  // close_valve(Valve::kOxRelease);
  // close_valve(Valve::kOxRelease);
  // close_valve(Valve::kOxN2Purge);
  // close_valve(Valve::kFuelRelease);

  /*
  init_pt_adc_spi();
  while (1) {
    // int64_t start = esp_timer_get_time();
    float psi_chamber = read_pt(Pt::kChamber);
    ESP_LOGI("PT", "Chamber Pressure: %.2f psi", psi_chamber);
    // float psi_eth_line = read_pt(Pt::kEthLine);
    // float psi_eth_n2 = read_pt(Pt::kEthN2Reg);
    // float psi_gox = read_pt(Pt::kGoxLine);
    // float psi_gox_reg = read_pt(Pt::kGoxReg);
    // float psi_ing_eth = read_pt(Pt::kInjectorEth);
    // float psi_inj_gox = read_pt(Pt::kInjectorGox);
    // int64_t end = esp_timer_get_time();
    // int64_t elapsed_us = end - start;
    // printf("Function took %lld us\n", elapsed_us);

    vTaskDelay(pdMS_TO_TICKS(1500));
  }*/

  demo_main();
}