#include <neopixel.h>

#define PIXEL_PIN D6
#define PIXEL_COUNT 40
#define PIXEL_TYPE WS2812B

const uint16_t ARTNET_PORT = 6454;
UDP artnet;

Adafruit_NeoPixel strip(PIXEL_COUNT, PIXEL_PIN, PIXEL_TYPE);

void setup() {
  strip.begin();
  strip.show();
  artnet.begin(ARTNET_PORT);
}

void loop() {
  int packetSize = artnet.parsePacket();
  if (packetSize > 18) { // Minimum Art-Net DMX packet size
    uint8_t buffer[530];
    int len = artnet.read(buffer, sizeof(buffer));
    if (len >= 18 && memcmp(buffer, "Art-Net", 7) == 0) {
      if (buffer[8] == 0x00 && buffer[9] == 0x50) { // OpCode ArtDMX
        int dmxLen = (buffer[16] << 8) | buffer[17];
        for (int i = 0; i < PIXEL_COUNT; i++) {
          int idx = 18 + i * 3;
          if (idx + 2 < 18 + dmxLen && idx + 2 < len) {
            uint8_t r = buffer[idx];
            uint8_t g = buffer[idx + 1];
            uint8_t b = buffer[idx + 2];
            strip.setPixelColor(i, strip.Color(r, g, b));
          }
        }
        strip.show();
      }
    }
  }
}
