#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/uart.h"

// bit 0 is the rightmost LED, bit 7 the leftmost
static const gpio_num_t LED_PINS[8] = {
    GPIO_NUM_13, GPIO_NUM_16, GPIO_NUM_17, GPIO_NUM_18,
    GPIO_NUM_19, GPIO_NUM_21, GPIO_NUM_22, GPIO_NUM_23
};

static void show(uint8_t b) {
    for (int i = 0; i < 8; i++) {
        gpio_set_level(LED_PINS[i], (b >> i) & 1);
    }
}

void app_main(void) {
    for (int i = 0; i < 8; i++) {
        gpio_reset_pin(LED_PINS[i]);
        gpio_set_direction(LED_PINS[i], GPIO_MODE_OUTPUT);
    }

    // self-test: all LEDs on for half a second, then off
    show(0xFF);
    vTaskDelay(pdMS_TO_TICKS(500));
    show(0x00);

    uart_config_t cfg = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    uart_driver_install(UART_NUM_0, 256, 0, 0, NULL, 0);
    uart_param_config(UART_NUM_0, &cfg);

    while (1) {
        uint8_t b;
        if (uart_read_bytes(UART_NUM_0, &b, 1, portMAX_DELAY) > 0) {
            show(b);                 // each byte received becomes the LED pattern
        }
    }
}
