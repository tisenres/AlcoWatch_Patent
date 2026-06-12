# Reference Numerals — ACN1408 Complete Specification (AI section)

Generated from the single-source numeral registry in `patent_style.py`. Every numeral
used in Figures 1-5 and the disclosure text is listed here exactly once.

| Reference numeral | Component |
|---|---|
| 100 | AI-based alcohol detection & vehicle ignition prevention system |
| 110 | Wearable smartwatch device |
| 112 | Photoplethysmography (PPG) sensor |
| 114 | Electrodermal activity (EDA), estimated/derived (no dedicated EDA sensor) |
| 116 | Skin / ambient temperature sensor |
| 118 | On-device inference engine (quantized TFLite) |
| 120 | AI / ML module performing on-device BAC estimation |
| 122 | Signal preprocessing and 10-timestep windowing |
| 124 | Feature tensor of shape [10 timesteps x 6 features] |
| 126 | Bidirectional LSTM (64 units) temporal-encoding stage |
| 128 | Temporal attention mechanism (Dense-tanh score, softmax, weighted sum) |
| 130 | Dense regression head (32 -> 16 -> 1) producing the BAC estimate |
| 132 | Climate-adaptive calibration (post-inference correction; not a network layer) |
| 140 | Secure Bluetooth Low Energy link (AES-256 per specification) |
| 150 | Vehicle control module |
| 152 | BLE receiver |
| 154 | Fail-safe decision / safety logic (default: ignition blocked) |
| 156 | Relay / MOSFET ignition switch |
| 160 | Ignition system / OBD-II / ECU interface |
| 170 | Status indicators (LED / buzzer) |
| 180 | Manual override button |
