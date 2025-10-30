#ifndef LORA_H_
#define LORA_H_

void demo_main();

typedef struct {
    float load_vout;
    uint16_t pt_reading;
} telemetry_t;

#endif  // LORA_H_