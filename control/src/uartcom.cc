#include "uartcom.h"
#include "lora.h"
#include "driver/usb_serial_jtag.h"
#include "esp_log.h"

static const char *TAG = "UARTCOM";

#ifdef CONFIG_HOME_SENDER
void home_com_monitor_task(void *pvParameters){
    usb_serial_jtag_driver_config_t config = USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    esp_err_t err = usb_serial_jtag_driver_install(&config);                    
    ESP_ERROR_CHECK(err);

    char buf[256];
    int len = 0;

    while (1){
        len = usb_serial_jtag_read_bytes((uint8_t*)buf, sizeof(buf)-1, pdMS_TO_TICKS(100));
        if (len > 0){
            buf[len] = '\0'; // Need to null terminate bc recieving from com
            ESP_LOGI(pcTaskGetName(NULL), "Received command: %s", buf);
            // TODO: Parse command to command_t structure
            command_t command;
            command.address = 0x01; // Example address
            command.target = 0x02;  // Example target
            command.command_type = 0x03; // Example command type
            // Send command to LoRa TX task
        }
    }
    vTaskDelete(NULL);
}
#endif // CONFIG_HOME_SENDER