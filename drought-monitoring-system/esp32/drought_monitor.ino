// Drought-monitoring sensor firmware.
// Communication: USB Serial only. No WiFi or HTTP code is used on the ESP32.

// ---- Pin configuration ----------------------------------------------------
#define SOIL_MOISTURE_PIN 36  // VP/GPIO36: analog soil-moisture input
#define WATER_LEVEL_PIN   34  // GPIO34: analog water-level input

// Common-cathode RGB LED pins.
#define RGB_RED_PIN   26
#define RGB_GREEN_PIN 27
#define RGB_BLUE_PIN  25

// ---- Sensor thresholds, ESP32 ADC range 0-4095 ---------------------------
// Water-level sensor.
const int WATER_MAX_ANOMALY = 3500;  // Excessive water or possible flooding
const int WATER_HIGH_THRESH = 1500;  // Water container is full
const int WATER_LOW_THRESH  = 300;   // Water container is low or empty

// Capacitive soil sensor: a lower reading means wetter soil.
const int MOISTURE_DISCONNECT = 50;    // Possible disconnected sensor
const int MOISTURE_WET_THRESH = 1500;  // Very wet soil
const int MOISTURE_DRY_THRESH = 2800;  // Dry soil that may need irrigation
const int MOISTURE_SHORT_CIR  = 4000;  // Possible short circuit

const unsigned long SERIAL_OUTPUT_INTERVAL_MS = 1000;

struct SensorState {
  const char* type;
  const char* message;
  const char* ledColor;
  int red;
  int green;
  int blue;
};

// Set the common-cathode RGB LED colour using PWM values from 0 to 255.
void setLedColor(int red, int green, int blue) {
  analogWrite(RGB_RED_PIN, red);
  analogWrite(RGB_GREEN_PIN, green);
  analogWrite(RGB_BLUE_PIN, blue);
}

SensorState evaluateReading(int water, int moisture) {
  // Hardware failure or possible flood.
  if (
    water >= WATER_MAX_ANOMALY
    || moisture <= MOISTURE_DISCONNECT
    || moisture >= MOISTURE_SHORT_CIR
  ) {
    return {
      "alert_hardware_or_flood",
      "ALERT: Sensor fault or possible flooding",
      "RED",
      255, 0, 0
    };
  }

  // Full water supply.
  if (water >= WATER_HIGH_THRESH) {
    if (moisture > MOISTURE_DRY_THRESH) {
      return {
        "warning_dry",
        "Full water supply, but the soil is dry and needs irrigation",
        "YELLOW",
        255, 255, 0
      };
    }
    if (moisture < MOISTURE_WET_THRESH) {
      return {
        "data_wet",
        "Full water supply and very wet soil",
        "WHITE",
        255, 255, 255
      };
    }
    return {
      "data_ideal",
      "Full water supply and ideal soil moisture",
      "GREEN",
      0, 255, 0
    };
  }

  // Medium water supply.
  if (water >= WATER_LOW_THRESH) {
    if (moisture > MOISTURE_DRY_THRESH) {
      return {
        "warning_dry_medium_water",
        "Medium water supply and dry soil",
        "ORANGE",
        255, 80, 0
      };
    }
    if (moisture < MOISTURE_WET_THRESH) {
      return {
        "data_wet_medium_water",
        "Medium water supply and wet soil",
        "LIGHT_BLUE",
        0, 100, 255
      };
    }
    return {
      "data_medium",
      "Medium water supply and moderate soil moisture",
      "CYAN",
      0, 255, 255
    };
  }

  // Low or empty water supply.
  if (moisture > MOISTURE_DRY_THRESH) {
    return {
      "alert_critical_dry_no_water",
      "CRITICAL: No water supply and dry soil",
      "PURPLE",
      255, 0, 255
    };
  }
  if (moisture < MOISTURE_WET_THRESH) {
    return {
      "warning_low_water_wet_soil",
      "Low water supply, but the soil is still wet",
      "PINK",
      255, 105, 180
    };
  }
  return {
    "warning_low_water",
    "Low water supply and moderate soil moisture",
    "BLUE",
    0, 0, 255
  };
}

// Print exactly one JSON object per line for the Python serial bridge.
void printJsonReading(
  const SensorState& state,
  int water,
  int moisture,
  unsigned long timestampMs
) {
  Serial.print("{\"type\":\"");
  Serial.print(state.type);
  Serial.print("\",\"water_level\":");
  Serial.print(water);
  Serial.print(",\"soil_moisture\":");
  Serial.print(moisture);
  Serial.print(",\"led_color\":\"");
  Serial.print(state.ledColor);
  Serial.print("\",\"timestamp_ms\":");
  Serial.print(timestampMs);
  Serial.println("}");
}

void setup() {
  Serial.begin(9600);
  analogSetAttenuation(ADC_11db);

  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(WATER_LEVEL_PIN, INPUT);
  pinMode(RGB_RED_PIN, OUTPUT);
  pinMode(RGB_GREEN_PIN, OUTPUT);
  pinMode(RGB_BLUE_PIN, OUTPUT);

  setLedColor(0, 0, 0);
  Serial.println("Drought monitor started in USB Serial mode.");
}

void loop() {
  int waterValue = analogRead(WATER_LEVEL_PIN);
  int moistureValue = analogRead(SOIL_MOISTURE_PIN);
  SensorState state = evaluateReading(waterValue, moistureValue);

  setLedColor(state.red, state.green, state.blue);

  Serial.print("Status: ");
  Serial.print(state.message);
  Serial.print(" | LED: ");
  Serial.println(state.ledColor);
  printJsonReading(state, waterValue, moistureValue, millis());

  delay(SERIAL_OUTPUT_INTERVAL_MS);
}
