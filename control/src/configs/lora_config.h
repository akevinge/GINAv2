#ifndef LORA_CONFIG_H_
#define LORA_CONFIG_H_

#define MAX_DRAIN_PER_CYCLE 20 // safety cap on packets drained per cycle
#define INTER_PACKET_DELAY_TICKS (pdMS_TO_TICKS(50)) // small delay between packets to avoid flooding
#define LORA_TRANSFER_RATE_HZ 10  // LoRa transfer rate in Hertz
#define LORA_MAX_PAYLOAD_SIZE 255  // Maximum LoRa payload size in bytes

#endif  // LORA_CONFIG_H_