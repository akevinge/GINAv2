#include "pt.h"

#include <algorithm>
#include <array>
#include <optional>

#include "configs/pt_config.h"
#include "esp_log.h"
#include "pt_adc.h"

const char* TAG = "PT";

class TareStore {
 public:
  // Returns singelton instance of TareStore.
  static TareStore& instance() {
    static TareStore instance;
    return instance;
  }

  // Sets the tare value for the specified pressure transducer.
  void set_tare_value(Pt pt, float tare_value) {
    tare_values[static_cast<size_t>(pt)] = tare_value;
  }

  // Gets the tare value for the specified pressure transducer.
  std::optional<float> get_tare_value(Pt pt) {
    return tare_values[static_cast<size_t>(pt)];
  }

 private:
  std::array<std::optional<float>, static_cast<size_t>(Pt::kPtMax)> tare_values;
};

void tare_all_pts(int samples, int delay_ms_between_samples) {
  for (size_t i = 0; i < static_cast<size_t>(Pt::kPtMax); ++i) {
    Pt pt = static_cast<Pt>(i);

    float total_voltage = 0.0f;
    for (int sample = 0; sample < samples; ++sample) {
      const PtConfig& pt_config = get_pt_config(pt);
      total_voltage += pt_adc_read_raw_voltage(pt_config.cs, pt_config.channel);
      // Super small delay to allow ADC to settle between samples like (1 ms).
      vTaskDelay(pdMS_TO_TICKS(delay_ms_between_samples));
    }
    float average_voltage = total_voltage / static_cast<float>(samples);
    ESP_LOGI(TAG, "Tared PT %d with average voltage: %.3f V",
             static_cast<int>(pt), average_voltage);

    TareStore::instance().set_tare_value(pt, average_voltage);
  }
}

float voltage_to_psi(const PtConfig& pt_config, float voltage) {
  return pt_config.max_pressure *
         (std::max(0.0f, voltage - pt_config.voltage_range.first) /
          (pt_config.voltage_range.second - pt_config.voltage_range.first));
}

float read_pt(Pt pt) {
  const PtConfig& pt_config = get_pt_config(pt);
  float tared_voltage = TareStore::instance().get_tare_value(pt).value_or(
      pt_config.voltage_range.first);
  float raw_voltage = pt_adc_read_raw_voltage(pt_config.cs, pt_config.channel);
  // Calculate the voltage adjusted for the tare.
  float effective_voltage =
      raw_voltage - (tared_voltage - pt_config.voltage_range.first);

#ifdef DEBUG_PT
  ESP_LOGI("PT", "Raw voltage for PT %d: %.3f V", static_cast<int>(pt),
           raw_voltage);
  ESP_LOGI("PT", "Effective voltage for PT %d: %.3f V", static_cast<int>(pt),
           effective_voltage);
#endif
  return voltage_to_psi(pt_config, effective_voltage);
}
