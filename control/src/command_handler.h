#pragma once

#include "lora.h"

enum class CommandType {
  kCloseAllValves,
};

void run_command(const command_t& command);

void command_exe_task(void* pvParameters);