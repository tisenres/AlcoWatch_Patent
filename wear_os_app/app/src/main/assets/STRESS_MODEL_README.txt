stress_model.tflite must be copied here after training:
  cp stress_detection/models/stress_model.tflite wear_os_app/app/src/main/assets/
Run: python -m stress_detection.training.train_stress_model (requires WESAD dataset)
