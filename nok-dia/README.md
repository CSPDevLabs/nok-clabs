# Telco Network Topology

## Overview

This Containerlab topology simulates a telco network environment featuring two Nokia SR-2SE routers, one Nokia IXR-S router, and four Nokia IXR-E2 routers. The SR-2SE nodes are configured with specific XCM and MDA components, and the nodes are interconnected to form a comprehensive network.

## Startup Configuration Files

The following nodes are initialized with specific startup configuration files:

*   **`sr-2se-1`**: `config/sr-2se-1-a-config.cfg`
*   **`sr-2se-2`**: `config/sr-2se-2-a-config.cfg`

## Configuration for Full Card Operation (Nokia SR-2SE)

To ensure full card operation for the Nokia SR-2SE nodes (`sr-2se-1` and `sr-2se-2`), specific power shelf and power module types must be configured. This is crucial for the system to recognize and power all installed components correctly.

Apply the following configuration commands to both `sr-2se-1` and `sr-2se-2` nodes:

```cli
/configure chassis router chassis-number 1 power-shelf 1 power-module 1 power-module-type ps-a-dc-6000
/configure chassis router chassis-number 1 power-shelf 1 power-module 2 power-module-type ps-a-dc-6000
/configure chassis router chassis-number 1 power-shelf 1 power-shelf-type ps-a4-shelf-dc
```

These commands define the power shelf as ps-a4-shelf-dc and configure two power modules as ps-a-dc-6000, enabling the full functionality of the installed cards.