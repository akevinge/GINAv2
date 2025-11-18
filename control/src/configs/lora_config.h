#ifndef LORA_CONFIG_H_
#define LORA_CONFIG_H_

//LoRaBegin Parameters
#define LORA_TX_POWER_DBM 22
#define LORA_TCXO_VOLTAGE 3.3
#define LORA_USE_REGULATOR_LDO 1
#if defined(CONFIG_AWAY_SENDER) || defined(CONFIG_HOME_RECEIVER)//No crosstalk
#define LORA_FREQUENCY_HZ 911000000
#endif
#if defined(CONFIG_HOME_SENDER) || defined(CONFIG_AWAY_RECIEVER)
#define LORA_FREQUENCY_HZ 913000000
#endif

//LoRaConfig Parameters
#define LORA_SPREADING_FACTOR
#define LORA_BANDWIDTH 6; // Maximum BW of 500 kHz at 6
#define LORA_CODING_RATE 1;
#define LORA_PREAMBLE_LENGTH 8;
#define LORA_PAYLOAD_LENGTH 0; // 0 for variable length
#define LORA_CRC_ON 1;
#define LORA_INVERT_IRQ 0;

//Telemetry parameters
#define MAX_DRAIN_PER_CYCLE 20 // safety cap on packets drained per cycle
#define INTER_PACKET_DELAY_TICKS (pdMS_TO_TICKS(50)) // small delay between packets to avoid flooding
#define LORA_TRANSFER_RATE_HZ 10  // LoRa transfer rate in Hertz
#define LORA_MAX_PAYLOAD_SIZE 255  // Maximum LoRa payload size in bytes


#define COMMAND_TARGET_SERVO 0x00
#define COMMAND_TARGET_IGNITER 0x01

#define COMMAND_ACTION_SERVO_CLOSE 0x00
#define COMMAND_ACTION_SERVO_OPEN 0x01
#define COMMAND_ACTION_SERVO_SET 0x02

#define COMMAND_ACTION_IGNITER_START 0x00

#define COMMAND_PARAM_SERVO_ALL 0xFF

#endif  // LORA_CONFIG_H_