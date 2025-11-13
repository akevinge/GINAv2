#include "driver/usb_serial_jtag.h"
#include "esp_log.h"

const static char *TAG = "UARTCOM";

#ifdef CONFIG_HOME_SENDER
void home_com_monitor_task(void *pvParameters);
#endif // CONFIG_HOME_SENDER