#include <Servo.h>
Servo gripper;
Servo wrist;
Servo twist;
Servo elbow;
Servo shoulder;
Servo servo06;
void setup() {
  // put your setup code here, to run once:
gripper.attach(44);
wrist.attach(42);
twist.attach(46);
elbow.attach(48);
shoulder.attach(50);
base.attach(52);

gripper_p0 = 90
gripper.write(gripper_p0)
wrist_p0 = 90
wrist.write(wrist_p0)
twist_p0 = 90
twist.write(twist_p0)
elbow_p0 = 90
elbow.write(elbow_p0)
shoulder_p0 = 90
shoulder.write(shoulder_p0)
base_p0 = 180
base.write(base_p0)
}


void loop() {
  // put your main code here, to run repeatedly:

}
