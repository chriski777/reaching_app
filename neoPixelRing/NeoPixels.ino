#include <Adafruit_NeoPixel.h>
#define PIN 6 // the Pin that will be our source of input

int totalPixels = 24;
Adafruit_NeoPixel strip = Adafruit_NeoPixel(totalPixels, PIN, NEO_RGBW + NEO_KHZ800);

uint32_t pureOff = strip.Color(0,0,0,0);
uint32_t pureWhite = strip.Color(0, 0, 0, 128);
uint32_t pureBrightWhite = strip.Color(0, 0, 0, 255);

void setup() {
  // put your setup code here, to run once:
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
}

void loop() {
  // put your main code here, to run repeatedly:
  setAllPixels(24,pureWhite);
  strip.show();
  delay(5000);
  setAllPixels(24,pureOff);
  strip.show();
  delay(5000);
}

void setAllPixels(int numPixel, uint32_t color) {
  for (int currPixel = 0; currPixel < numPixel; currPixel++) {
    strip.setPixelColor(currPixel, color);
  }
}
