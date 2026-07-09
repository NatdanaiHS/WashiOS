# WashiOS

WashiOS is an early-stage embedded software prototype for CubeSat onboard computer experiments. It is built around FreeRTOS, C++, and PlatformIO, with a focus on STM32-based development boards.

The project explores how to structure CubeSat onboard software using RTOS tasking, hardware abstraction, and safety-related components. It is not flight-qualified software.

## Current Focus

* FreeRTOS-based task structure for CubeSat onboard software
* Hardware abstraction layer for board portability
* STM32-specific board support
* Fault logging
* Task-health monitoring
* Watchdog handling
* Boot failure handling
* Telemetry framing

## Target Platform

The current main target is STM32G431RB. The project is developed using PlatformIO.

## Project Status

This project is still an early-stage prototype and learning/research work. The architecture and implementation may change as requirements become clearer.

## Notes

This repository is shared to show the direction of my work on CubeSat onboard computer software. It should not be treated as production-ready or flight-qualified software.
