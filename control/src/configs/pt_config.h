#pragma once

#include <driver/gpio.h>
#include <esp32_driver_mcp320x/mcp320x.h>

#include <utility>

#include "pt.h"

// Uncomment to enable pressure transducer debug logging.
// #define DEBUG_PT

struct PtConfig {
  // Chip select which identifies which ADC to read from.
  gpio_num_t cs;
  // Channel which identifies which channel to read on the ADC.
  mcp320x_channel_t channel;
  // Voltage range representing 0 to max pressure.
  std::pair<float, float> voltage_range;
  // Max pressure represented by voltage_range[1];
  uint16_t max_pressure;
};

// Configuration for various pressure transducers.
// !!!! READ BEFORE MODIFYING !!!!
// Ensure the PT type is in the same order as Valve enum variants.
// Pt enum variants are used to index this array. See `get_pt_config`.
constexpr PtConfig PT_CONFIGS[] = {
    // kChamber
    {
        .cs = GPIO_NUM_4,
        .channel = MCP320X_CHANNEL_0,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 1000,
    },
    // kInjectorGox,
    {
        .cs = GPIO_NUM_5,
        .channel = MCP320X_CHANNEL_1,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 1000,
    },
    // kInjectorEth,
    {
        .cs = GPIO_NUM_5,
        .channel = MCP320X_CHANNEL_2,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 1000,
    },
    // kEthN2Reg,
    {
        .cs = GPIO_NUM_5,
        .channel = MCP320X_CHANNEL_3,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 1000,
    },
    // kEthLine,
    {
        .cs = GPIO_NUM_7,
        .channel = MCP320X_CHANNEL_0,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 1000,
    },
    // kGoxReg,
    {
        .cs = GPIO_NUM_7,
        .channel = MCP320X_CHANNEL_1,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 3000,
    },
    // kGoxLine
    {
        .cs = GPIO_NUM_7,
        .channel = MCP320X_CHANNEL_2,
        .voltage_range = {0.5, 4.5},
        .max_pressure = 1000,
    },
};

// Gets the PtConfig for the specified Pt.
constexpr const PtConfig& get_pt_config(Pt pt) {
  return PT_CONFIGS[static_cast<int>(pt)];
}
