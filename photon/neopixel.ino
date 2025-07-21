#include <neopixel.h>

#define PIXEL_PIN D6
#define PIXEL_COUNT 40
#define PIXEL_TYPE WS2812B

Adafruit_NeoPixel strip(PIXEL_COUNT, PIXEL_PIN, PIXEL_TYPE);

void setup() {
  strip.begin();
  strip.show();
  Particle.function("setColor", setColor);
}

void loop() {}

int setColor(String command) {
  int r, g, b;
  if (sscanf(command.c_str(), "%d,%d,%d", &r, &g, &b) == 3) {
    for (int i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
    return 1;
  }
  return -1;
}
