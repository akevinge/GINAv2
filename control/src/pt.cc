#include "pt.h"

#include <algorithm>
#include <array>

#include "configs/pt_config.h"
#include "esp_log.h"
#include "pt_adc.h"

float voltage_to_psi(const PtConfig& pt_config, float voltage) {
  return pt_config.max_pressure *
         (std::max(0.0f, voltage - pt_config.voltage_range.first) /
          (pt_config.voltage_range.second - pt_config.voltage_range.first));
}

float read_pt(Pt pt) {
  const PtConfig& pt_config = get_pt_config(pt);
  float raw_voltage = pt_adc_read_raw_voltage(pt_config.cs, pt_config.channel);

#ifdef DEBUG_PT
  ESP_LOGI("PT", "Raw voltage for PT %d: %.3f V", static_cast<int>(pt),
           raw_voltage);
#endif
  return voltage_to_psi(pt_config, raw_voltage);
}

uint16_t read_pt_int(Pt pt) {
  const PtConfig& pt_config = get_pt_config(pt);
  float raw_voltage = pt_adc_read_raw_voltage_int(pt_config.cs, pt_config.channel);
#ifdef DEBUG_PT
  ESP_LOGI("PT", "Raw voltage for PT %d: %.3f V", static_cast<int>(pt),
           raw_voltage);
#endif
  return raw_voltage;
}