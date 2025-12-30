# Product Overview

This is an **Electricity Meter Management** system built as a Frappe application. The system manages electricity meter readings, customer billing, and electricity type configurations.

## Core Features

- **Meter Movement Tracking**: Record and manage electricity meter readings with period-based data collection
- **Customer Management**: Integration with Frappe's Customer doctype with custom fields for meter numbers and readings
- **Electricity Type Configuration**: Define different electricity types with pricing and item information
- **Automated Billing**: Calculate consumption differences and generate bills with Arabic language support
- **Print Functionality**: Generate printable bills in Arabic with custom formatting

## Key Business Logic

- Meter readings are tracked through "Meter Movement" documents that contain child tables of customer readings
- When a Meter Movement is submitted, it automatically updates each customer's meter reading
- The system prevents negative consumption (current reading less than previous reading)
- Bills are generated with consumption calculation (current - previous reading) × price per unit
- Arabic language interface with RTL support for printing and UI elements

## Target Users

Electricity utility companies or cooperatives managing customer meter readings and billing in Arabic-speaking regions.