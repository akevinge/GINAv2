#pragma once

#include <esp_err.h>

#include <cstdint>

void init_load_cell();

esp_err_t read_raw_load_cell(uint32_t* value);