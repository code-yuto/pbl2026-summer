// ---- Pins Configured -------------------------------------------------------
#define AOUT_PIN      36 // Chân VP (GPIO36) nhận tín hiệu Analog độ ẩm đất
#define SIGNAL_PIN    34 // Chân GPIO34 nhận tín hiệu cảm biến mực nước

// Common-cathode RGB LED.
#define RGB_RED_PIN   26 // Chân điều khiển LED Đỏ
#define RGB_GREEN_PIN 27 // Chân điều khiển LED Xanh lá
#define RGB_BLUE_PIN  25 // Chân điều khiển LED Xanh dương

// ---- Ngưỡng cài đặt (ADC 0 - 4095) ---------------------------------------
// Cảm biến mực nước
const int WATER_MAX_ANOMALY   = 3500; // Nước quá cao / Ngập lụt
const int WATER_HIGH_THRESH    = 1500; // Nước đầy
const int WATER_LOW_THRESH     = 300;  // Nước thấp / Cạn

// Cảm biến độ ẩm đất (Đã hiệu chỉnh theo cảm biến thực tế: Giá trị CÀNG CAO = CÀNG ẨM)
const int MOISTURE_DISCONNECT  = 50;   // Bất thường: Mất kết nối dây
const int MOISTURE_DRY_THRESH  = 150;  // Đất khô / Cần tưới
const int MOISTURE_WET_THRESH  = 600;  // Đất ướt / Ẩm cao
const int MOISTURE_SHORT_CIR   = 4000; // Bất thường: Chập mạch

int waterValue = 0;
int moistureValue = 0;

// Hàm bật màu tùy chỉnh cho LED RGB bằng PWM (analogWrite) để phối màu chính xác
void setLedColor(int r, int g, int b) {
  analogWrite(RGB_RED_PIN,   r);
  analogWrite(RGB_GREEN_PIN, g);
  analogWrite(RGB_BLUE_PIN,  b);
}

// The LED only ever shows one of these 4 colors, matching the risk_level
// tiers used by the backend/dashboard (normal / medium / high+critical),
// plus a hardware-fault color that has no equivalent on the dashboard.
// Only the LED color is simplified this way; the JSON "type" field sent to
// the backend keeps its original fine-grained value in every branch below,
// so nothing on the backend/dashboard side needs to change.
void ledHardwareFault() { setLedColor(255, 0, 0); }   // RED    - sensor fault / flood, do not trust reading
void ledNoProblem()     { setLedColor(0, 255, 0); }   // GREEN  - matches backend risk_level "normal"
void ledCaution()       { setLedColor(255, 255, 0); } // YELLOW - matches backend risk_level "medium"
void ledNeedsAttention(){ setLedColor(255, 80, 0); }  // ORANGE - matches backend risk_level "high"/"critical"

// In chuỗi JSON gửi về Serial
void printReading(const char* status_type, int water, int moisture, const char* color_name) {
  Serial.print("{\"type\":\"");
  Serial.print(status_type);
  Serial.print("\",\"water_level\":");
  Serial.print(water);
  Serial.print(",\"soil_moisture\":");
  Serial.print(moisture);
  Serial.print(",\"led_color\":\"");
  Serial.print(color_name);
  Serial.print("\",\"timestamp_ms\":");
  Serial.print(millis());
  Serial.println("}");
}

void setup() {
  Serial.begin(9600);
  analogSetAttenuation(ADC_11db);

  pinMode(AOUT_PIN, INPUT);
  pinMode(SIGNAL_PIN, INPUT);

  pinMode(RGB_RED_PIN, OUTPUT);
  pinMode(RGB_GREEN_PIN, OUTPUT);
  pinMode(RGB_BLUE_PIN, OUTPUT);
  
  setLedColor(0, 0, 0); // Tắt LED ban đầu
}

void loop() {
  waterValue = analogRead(SIGNAL_PIN);
  moistureValue = analogRead(AOUT_PIN);

  // 1. Kiểm tra sự cố phần cứng / Lỗi ngập lụt
  if (waterValue >= WATER_MAX_ANOMALY || 
      moistureValue <= MOISTURE_DISCONNECT || 
      moistureValue >= MOISTURE_SHORT_CIR) {
      
    ledHardwareFault();
    Serial.println(">>> TRẠNG THÁI: [BÁO ĐỘNG] Lỗi cảm biến hoặc ngập lụt! | LED: DO (Machine anomaly)");
    printReading("alert_hardware_or_flood", waterValue, moistureValue, "RED");
  }
  // 2. NƯỚC ĐẦY (water >= 1500)
  else if (waterValue >= WATER_HIGH_THRESH) {
    if (moistureValue < MOISTURE_DRY_THRESH) {
      ledNeedsAttention();
      Serial.println(">>> TRẠNG THÁI: Nước đầy - Đất khô (Cần tưới) | LED: CAM (Needs attention)");
      printReading("warning_dry", waterValue, moistureValue, "ORANGE");
    }
    else if (moistureValue > MOISTURE_WET_THRESH) {
      ledNoProblem();
      Serial.println(">>> TRẠNG THÁI: Nước đầy - Đất rất ướt | LED: XANH LA (No problem)");
      printReading("data_wet", waterValue, moistureValue, "GREEN");
    }
    else {
      ledNoProblem();
      Serial.println(">>> TRẠNG THÁI: Nước đầy - Đất độ ẩm vừa (Lý tưởng) | LED: XANH LA (No problem)");
      printReading("data_ideal", waterValue, moistureValue, "GREEN");
    }
  }
  // 3. NƯỚC VỪA (300 <= water < 1500)
  else if (waterValue >= WATER_LOW_THRESH) {
    if (moistureValue < MOISTURE_DRY_THRESH) {
      ledNeedsAttention();
      Serial.println(">>> TRẠNG THÁI: Nước trung bình - Đất khô | LED: CAM (Needs attention)");
      printReading("warning_dry_medium_water", waterValue, moistureValue, "ORANGE");
    }
    else if (moistureValue > MOISTURE_WET_THRESH) {
      ledCaution();
      Serial.println(">>> TRẠNG THÁI: Nước trung bình - Đất ướt | LED: VANG (Caution)");
      printReading("data_wet_medium_water", waterValue, moistureValue, "YELLOW");
    }
    else {
      ledCaution();
      Serial.println(">>> TRẠNG THÁI: Nước trung bình - Đất vừa | LED: VANG (Caution)");
      printReading("data_medium", waterValue, moistureValue, "YELLOW");
    }
  }
  // 4. NƯỚC CẠN (water < 300)
  else {
    if (moistureValue < MOISTURE_DRY_THRESH) {
      ledNeedsAttention();
      Serial.println(">>> TRẠNG THÁI: [CỰC KỲ NGUY HIỂM] Hết nước & Đất khô! | LED: CAM (Needs attention)");
      printReading("alert_critical_dry_no_water", waterValue, moistureValue, "ORANGE");
    }
    else if (moistureValue > MOISTURE_WET_THRESH) {
      ledNeedsAttention();
      Serial.println(">>> TRẠNG THÁI: Cạn nước trong bình - Đất ướt | LED: CAM (Needs attention)");
      printReading("warning_low_water_wet_soil", waterValue, moistureValue, "ORANGE");
    }
    else {
      ledNeedsAttention();
      Serial.println(">>> TRẠNG THÁI: Cạn nước trong bình - Đất vừa | LED: CAM (Needs attention)");
      printReading("warning_low_water", waterValue, moistureValue, "ORANGE");
    }
  }

  delay(1000);
}