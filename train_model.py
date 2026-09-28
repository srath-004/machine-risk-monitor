import json


model_rules = {
    "temp_high_threshold": 80,
    "pressure_high_threshold": 120,
    "vibration_high_level": "High"
}


with open('risk_model.json', 'w') as f:
    json.dump(model_rules, f)

print("Rule-based ML model configuration saved successfully as risk_model.json!")