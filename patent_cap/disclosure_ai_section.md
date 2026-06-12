# AI Framework & Model — Disclosure Text for the Complete Specification (ACN1408)

*Drop-in technical-disclosure section for the Form-2 Complete Specification. Patent-style,
enablement-level. Reference numerals match `reference_numerals.md` and Figures 1–5. Where
the as-built embodiment differs from the provisional, see `provisional_reconciliation.md`
(the patent agent should reconcile the claim language accordingly).*

---

## 1. System overview (FIG. 1)

The AI-based alcohol detection and vehicle ignition prevention system (100) comprises a
wearable smartwatch device (110) and a vehicle control module (150) coupled by a secure
Bluetooth Low Energy link (140). The smartwatch (110) carries a photoplethysmography
sensor (112), an electrodermal-activity channel (114), and a skin/ambient temperature
sensor (116). An on-device inference engine (118) executes an AI/ML module (120) that
estimates blood alcohol concentration (BAC) from the sensed physiological signals.

The estimated BAC, together with a confidence value and status flags, is transmitted as a
periodic status packet over the secure link (140) to the vehicle control module (150),
which comprises a BLE receiver (152), fail-safe decision logic (154), and a relay/MOSFET
ignition switch (156) coupled to the vehicle ignition / OBD-II / ECU interface (160).
Status indicators (170) and a manual override button (180) are provided. The decision
logic (154) is fail-safe: ignition is **blocked by default** and is enabled only while all
permissive conditions hold.

## 2. AI framework / signal-processing pipeline (FIG. 3)

In operation, raw signals from the sensors (112, 114, 116) are preprocessed and segmented
into fixed-length temporal windows of ten time steps (122), forming a feature tensor (124)
of shape [10 time steps × 6 features]. The six features comprise a PPG value, a PPG signal
quality measure, an electrodermal-activity value, a skin temperature, an ambient
temperature, and a humidity value. The feature tensor (124) is supplied to a trained
neural network (126, 128, 130) that produces a raw BAC estimate.

The raw BAC estimate is then adjusted by a climate-adaptive calibration stage (132). The
calibration (132) is a **deterministic post-inference correction** applied to the model
output using region-specific temperature and humidity coefficients; it is **not** a layer
of the trained neural network. The resulting calibrated BAC is compared by the decision
logic (154) against a legal threshold of 0.08 g/dL; the allow/block determination, with a
confidence value, is transmitted over the secure link (140) to control the ignition (160).

## 3. Neural-network model architecture (FIG. 4)

The trained model receives the feature tensor (124) of shape [B, 10, 6] and processes it
through a bidirectional long short-term memory (BiLSTM) stage (126) of 64 units, producing
a temporally-encoded representation of shape [B, 10, 128], followed by a dropout stage
(rate 0.3).

A temporal attention mechanism (128) operates on the encoded sequence: a dense projection
with a hyperbolic-tangent activation computes per-time-step scores, a softmax produces
attention weights over the ten time steps, and a weighted sum across time produces a
128-dimensional attention context vector. The context vector is passed through a dense
regression head (130) — a 32-unit rectified-linear layer, a dropout stage (rate 0.3), a
16-unit rectified-linear layer, and a final single-unit linear layer — that outputs the
BAC estimate in g/dL.

**Safety-prioritized training.** The model is trained with an asymmetric loss function in
which false-negative errors (predicting a sober reading when the true BAC is above the
threshold) are penalized **30×** more heavily than false-positive errors. This biases the
system toward the safety-critical suppression of missed-intoxication events.

**On-device deployment.** The trained model is quantized and deployed on the smartwatch as
a TensorFlow Lite model executed by the on-device inference engine (118). Because the
network contains LSTM operations, the converted model retains the requisite TensorFlow
Lite operator set (SELECT_TF_OPS) for on-device execution.

## 4. System operation and verification sequence (FIG. 2)

The smartwatch (110) continuously supplies sensor data to the AI/BAC module (120), which
estimates BAC and compares it to the 0.08 g/dL threshold and transmits a BAC status packet
over the secure link (140) at a regular interval. The vehicle module (150) blocks ignition
by default; upon an override attempt it requests verification, prompting a fresh
sensor-data recheck, and otherwise maintains the ignition block.

## 5. Fail-safe vehicle-control state machine (FIG. 5)

The decision logic (154) implements a fail-safe state machine. The initial/default state
upon power-on is IGNITION_BLOCKED. Ignition is enabled (IGNITION_ALLOWED) only while the
link is active, a recent BAC update has been received, the estimated BAC is below 0.08
g/dL, and the watch is worn. Loss of communication beyond a timeout transitions to
CONNECTION_LOST and re-blocks; removal of the watch or stale data re-blocks. A manual
override (180), engaged by a sustained button hold, transitions to a time-limited, logged
OVERRIDE_ACTIVE state that automatically reverts to IGNITION_BLOCKED.

---

## Notes for the patent agent (accuracy)

- The electrodermal-activity channel (114) is **derived/estimated** from heart-rate
  variability in the present embodiment (most consumer smartwatches lack a dedicated EDA
  sensor); it is not represented as a directly-sensed EDA measurement.
- BAC is **inferred from physiological proxies** by the trained model; the present
  embodiment does not use a transdermal alcohol sensor.
- The model is trained on **physiologically-modeled synthetic data** in the present
  embodiment.
- The 0.08 g/dL threshold is a fixed legal threshold in the present embodiment.
- The secure link (140) is specified to use AES-256; see `provisional_reconciliation.md`
  for the implementation status.
