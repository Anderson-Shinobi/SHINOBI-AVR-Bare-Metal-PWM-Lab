/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Anderson Nogueira
 *
 * SHINOBI Interactive Lab — AVR Timer1 PWM, GPIO and UART
 * Target: Arduino Uno R3 / ATmega328P @ 16 MHz
 *
 * Bare-metal peripheral configuration; no pinMode, digitalWrite,
 * analogWrite, delay, Serial or heap allocation. Arduino provides only
 * the startup wrapper that calls setup() and loop() in the Wokwi editor.
 */
#ifndef F_CPU
#define F_CPU 16000000UL
#endif

#include <avr/io.h>
#include <util/delay.h>
#include <stdint.h>

namespace {
constexpr uint16_t kUartDivisor = 103; // 9600 bps @ 16 MHz, U2X0 = 0
constexpr uint8_t kDutySteps[] = {26, 128, 230};
const char* const kLabels[] = {"10%", "50%", "90%"};

void uart_write(char c) {
  while ((UCSR0A & _BV(UDRE0)) == 0) {
    // Poll transmit buffer; no Arduino Serial dependency.
  }
  UDR0 = static_cast<uint8_t>(c);
}

void uart_print(const char* value) {
  while (*value != '\0') uart_write(*value++);
}

void configure_uart() {
  UCSR0A = 0; // Normal speed
  UBRR0H = static_cast<uint8_t>(kUartDivisor >> 8);
  UBRR0L = static_cast<uint8_t>(kUartDivisor);
  UCSR0B = _BV(TXEN0);
  UCSR0C = _BV(UCSZ01) | _BV(UCSZ00); // 8 data bits, 1 stop bit
}

void configure_timer1() {
  // PB1 -> Arduino D9 (OC1A), PB5 -> onboard status LED (D13).
  DDRB |= _BV(DDB1) | _BV(DDB5);
  PORTB &= static_cast<uint8_t>(~_BV(PORTB5));

  // Timer1 Fast PWM 8-bit (mode 5, TOP = 255).
  // Non-inverting OC1A, prescaler = 64.
  // fPWM = 16 MHz / (64 * 256) = 976.5625 Hz.
  TCCR1A = _BV(COM1A1) | _BV(WGM10);
  TCCR1B = _BV(WGM12) | _BV(CS11) | _BV(CS10);
  TCNT1 = 0;
  OCR1A = kDutySteps[0];
}
} // namespace

void setup() {
  configure_uart();
  configure_timer1();
  uart_print("SHINOBI AVR / Timer1 PWM @ 976.56 Hz\r\n");
}

void loop() {
  static uint8_t phase = 0;
  OCR1A = kDutySteps[phase];
  PORTB ^= _BV(PORTB5); // Prove GPIO toggling independently of Timer1 PWM.

  uart_print("OC1A D9 duty target: ");
  uart_print(kLabels[phase]);
  uart_print("\r\n");

  phase = (phase + 1) % 3;
  _delay_ms(1000); // AVR-libc busy wait (not Arduino delay).
}
