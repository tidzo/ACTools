# Advanced Controller Tools
Tools for users of game controllers with many buttons and toggles, such as the Thrustmaster Warthog.  

## 1. Named Controllers for FreePIE

[FreePIE](http://andersmalmgren.github.io/FreePIE/) is  a programmable input emulator.  You can do stuff like this:

```python
myStick = joystick[0]
if myStick.getDown(0) and myStick.getDown(1):
  keyboard.setPressed(Key.G)
```
("if buttons one and two on my first joystick are pressed, then emulate pressing the letter G on the keyboard")

That's fine until you get a stick with tons of buttons - like the Warthog.  Remembering which button is which, as well as handling the fact that to get the value of the button that makes light number 17 come on in joy.cpl needs you to do getDown(16), can get confusing pretty fast.  That's why I wrote *Named Controllers for FreePIE* which will let you do this:

```python
throttle=namedcontrollers.WarthogThrottle()

if throttle.toggles.eac=='ARM' and throttle.toggles.rdr=='NRM' and throttle.buttons.autopilot:
  
  #eject
  keyboard.setPressed(Key.LeftAlt)
  keyboard.setPressed(Key.L)
```

(If the 'EAC' toggle switch is set to 'ARM' (up), AND the 'RDR' toggle switch is set to 'NRM' (up), AND the 'Autopilot engage/disengage button is pressed, then emulate pressng LeftAlt plus L (the default eject key in [Star Citizen](https://robertsspaceindustries.com/enlist?referral=STAR-DLML-6LDN) (*referral link*).
