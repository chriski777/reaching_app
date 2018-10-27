import processing.serial.*;
Serial mySerial;
import java.text.*;
long now;
PrintWriter output;
DateFormat formatter = new SimpleDateFormat("yyyy_MM_dd_hh_mm_ss_SSS");

void setup() {
   mySerial = new Serial( this, Serial.list()[0], 115200);
   output = createWriter( "lick_data.txt" );
}
void draw() {
    if (mySerial.available() > 0 ) {
         String input = mySerial.readStringUntil('\n').trim();
         now = System.currentTimeMillis();
         if ( input != null && !input.isEmpty()) {
              output.println(formatter.format(now).substring(0,23) + ", " + input );
         }
    }
}

void keyPressed() {
    output.flush();  // Writes the remaining data to the file
    output.close();  // Finishes the file
    exit();  // Stops the program
}
