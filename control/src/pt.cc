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

uint16_t read_pt(Pt pt) {
  const PtConfig& pt_config = get_pt_config(pt);
  float raw_voltage = pt_adc_read_raw_voltage(pt_config.cs, pt_config.channel);
  return voltage_to_psi(pt_config, raw_voltage);
}