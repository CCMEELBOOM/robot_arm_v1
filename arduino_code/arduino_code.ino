
#include <Servo.h>
Servo gripper;
Servo wrist;
Servo twist;
Servo elbow;
Servo shoulder;
Servo base;

int gripper_p0 = 45;
int wrist_p0 = 90;
int twist_p0 = 90;
int elbow_p0 = 180;
int shoulder_p0 = 180;
int base_p0 = 90;

int minA[6] = {0, 0, 0, 0, 0, 0};
int maxA[6] = {45, 180, 180, 180, 180, 180};
  // Set limits for servos

int clampAngle(int j, int a) {
  // We define j as the servo and a as the angle.
  // Claping angles ensures that the servos remain within the 0 to 180 degree bounds.
  if (a < minA[j]) a = minA[j];
  if (a > maxA[j]) a = maxA[j];
  return a; 
}

void writeJoint( int j, int a){; 
  a = clampAngle(j,a); 
  switch (j) {
    case 0: gripper.write(a);  break;
    case 1: wrist.write(a);    break;
    case 2: twist.write(a);    break;
    case 3: elbow.write(a);    break;
    case 4: shoulder.write(a); break;
    case 5: base.write(a);     break;
    default: break;
  }
}
void setup() {
  Serial.begin(115200);
  // void means that the funciton doesn't return a value
  // put your setup code here, to run once:
  gripper.attach(44);
  wrist.attach(42);
  twist.attach(46);
  elbow.attach(48);
  shoulder.attach(50);
  base.attach(52);

  gripper.write(gripper_p0);
  wrist.write(wrist_p0);
  twist.write(twist_p0);
  elbow.write(elbow_p0);
  shoulder.write(shoulder_p0);
  base.write(base_p0);
}

void loop() {
  if (!Serial.available()) return; 
  
  String line = Serial.readStringUntil('\n');
  // \n becomes whatever value the Java script sends like J 3 120; Joint 3 120 degs
  line.trim();
  if (line.length() == 0) return;

  char cmd; 
  // cmd command letter becomes character
  int joint, angle; 
  // joint and angle becomes integer
  // Parse: <char> <int> <int>
  int parsed = sscanf(line.c_str(), "%c %d %d", &cmd, &joint, &angle);
    // sscanf parses a string that comes in based on the fomat pattern; 
    // here it expects a character %c, and two integers %d %d 
  if (parsed == 3 && (cmd == 'J' || cmd == 'j')) {
    if (joint >= 0 && joint < 6) {
      writeJoint(joint, angle);
    }
  }
}

