#pragma once

#include <driver/uart.h>

// UART peripheral to use (UART0 connected to CP210x)
constexpr uart_port_t UART_PORT = UART_NUM_0;

// Default baud rate
constexpr int UART_BAUD_RATE = 115200;

// Data bits configuration (8-bit data)
constexpr uart_word_length_t UART_DATA_BITS = UART_DATA_8_BITS;

// Parity configuration
constexpr uart_parity_t UART_PARITY = UART_PARITY_DISABLE;

// Stop bits configuration
constexpr uart_stop_bits_t UART_STOP_BITS = UART_STOP_BITS_1;

// Flow control
constexpr uart_hw_flowcontrol_t UART_FLOW_CTRL = UART_HW_FLOWCTRL_DISABLE;

// TX/RX buffer size in bytes
constexpr int UART_TX_BUF_SIZE = 2048;
constexpr int UART_RX_BUF_SIZE = 2048;

// Timeout for uart_read_bytes in milliseconds
constexpr TickType_t UART_READ_TIMEOUT_MS = 100;

// Optional: pins (use NO_CHANGE if using default)
constexpr int UART_TX_PIN = UART_PIN_NO_CHANGE;
constexpr int UART_RX_PIN = UART_PIN_NO_CHANGE;
constexpr int UART_RTS_PIN = UART_PIN_NO_CHANGE;
constexpr int UART_CTS_PIN = UART_PIN_NO_CHANGE;
