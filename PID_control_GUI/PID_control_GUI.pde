import processing.serial.*;
import controlP5.*;
import java.util.*;

int baud;
Serial mySerial;

ControlP5 cp5;
Textlabel myTextlabelA;
String selectedPort = null;

void setup() {
  size(400, 400); //size(x_width,y_height)
  cp5 = new ControlP5(this);
  List COM_ports = Arrays.asList(Serial.list());
  cp5.addScrollableList("dropdown")
     .setPosition(25, 25)
     .setSize(200, 100)
     .setBarHeight(20)
     .setItemHeight(20)
     .addItems(COM_ports)
     .setOpen(false) 
  ;
  myTextlabelA = new Textlabel(cp5,"COM Port",5,25,400,200);

}

void draw() {
  background(240);
  if( selectedPort != null){
  }
  myTextlabelA.draw(this); 
}

void dropdown(int n) {
  /* request the selected item based on index n */
  println(n, cp5.get(ScrollableList.class, "dropdown").getItem(n));
  
  /* here an item is stored as a Map  with the following key-value pairs:
   * name, the given name of the item
   * text, the given text of the item by default the same as name
   * value, the given value of the item, can be changed by using .getItem(n).put("value", "abc"); a value here is of type Object therefore can be anything
   * color, the given color of the item, how to change, see below
   * view, a customizable view, is of type CDrawable 
   */
  
   CColor c = new CColor();
  c.setBackground(color(255,0,0));
  cp5.get(ScrollableList.class, "dropdown").getItem(n).put("color", c);  
  selectedPort = cp5.get(ScrollableList.class, "dropdown").getItem(n).get("name").toString();
}
