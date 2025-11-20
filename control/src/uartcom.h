#ifdef CONFIG_HOME_SENDER
void home_com_monitor_task(void *pvParameters);
#endif // CONFIG_HOME_SENDER
#ifdef CONFIG_HOME_RECEIVER
void telemetry_uartcom_task(void *pvParameters);
#endif // CONFIG_HOME_RECEIVER