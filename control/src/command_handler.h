#pragma once

#include "lora.h"

enum class CommandType {
  kCloseAllValves,
};

void run_command(const command_t& command);

// Renamed to avoid colliding with the main command executor implementation
void command_handler_task(void* pvParameters);