# Advanced Controller Tools
Tools for users of game controllers with many buttons and toggles, such as the Thrustmaster Warthog.

## 1. Named Controllers for FreePIE

###Introduction
[FreePIE](http://andersmalmgren.github.io/FreePIE/) is  a programmable input emulator which is lets you do stuff like this:

```python
myStick = joystick[0]
if myStick.getDown(0) and myStick.getDown(1):
  keyboard.setPressed(Key.G)
```
("if buttons one and two on my first joystick are pressed, then emulate pressing the letter G on the keyboard")

That's fine until you get a stick with tons of buttons - like the Warthog.  Remembering which button is which, as well as handling the fact that to get the value of the button that makes light number 17 come on in joy.cpl needs you to do getDown(16), can get confusing pretty fast.  That's why I wrote *Named Controllers for FreePIE* which will let you do this:

```python
throttle=namedcontrollers.WarthogThrottle()

if throttle.toggles.eac=='ARM' and throttle.toggles.rdr=='NRM' and throttle.buttons.autopilot():
  
  #eject
  keyboard.setPressed(Key.LeftAlt)
  keyboard.setPressed(Key.L)
```

(If the 'EAC' toggle switch is set to 'ARM' (up), AND the 'RDR' toggle switch is set to 'NRM' (up), AND the 'Autopilot engage/disengage button is pressed, then emulate pressng LeftAlt plus L (the default eject key in [Star Citizen](https://robertsspaceindustries.com/enlist?referral=STAR-DLML-6LDN) (*referral link*).

This project currently provides named buttons, toggles, axes and hat switches for the TM Warthog flight stick and throttle.  I will be adding support for my TM Hotas-X shortly, and guidance on adding support for other controls is below.

Using FreePIE and this Named Controllers tool, it is possible to configure complex logic for control schemes, without using TARGET or equivalent software.  It remains to be seen whether this eventual solution is in fact more difficult to use than TARGET!

###Installation

1. Install [FreePIE](http://andersmalmgren.github.io/FreePIE/)
2. Copy namedcontrollers.py from this project to the 'pylib' folder of your FreePIE installation.  For me, that means **c:\Program Files (x86)\FreePIE\pylib**, but YMMV.  
3. Launch FreePIE and load one of the files in the examples directory of this project.

###Usage

Currently, FreePIE needs to know the ID of each joystick to be able to work with it.  You can discover this ID by looking in Windows' Game Controllers control panel (joy.cpl).  The first item listed should normally be accessible in FreePIE as **joystick[0]**.  The third item would be **joystick[2]**.  This is likely to change in a future version, as discussed in [this forum post](http://www.mtbs3d.com/phpBB/viewtopic.php?f=139&t=21709&sid=766538289af1a35823338d9521f3b706) but for now, you need to hardcode that ID I'm afraid.

####Boilerplate
Your FreePIE script needs to include something like this at the beginning:

````python
if starting:
  import namedcontrollers
  
  stickID=0
  throttleID=1
  
  stick=namedcontrollers.WarthogStick(joystick[stickID])
  thottle=namedcontrollers.WarthogThrottle(joystick[throttleID])
````

####Accessing controls
All of the controls are accessible under one of

* throttle.buttons.button_name()
* throttle.toggles.switch_name()
* throttle.axes.axis_name()
* throttle.hats.hat_name()

(and the same for the stick, although it has no toggles)

Note the () in each case.  While there might be a way around that (using python's magic methods), that doesn't seem to work in the FreePIE diagnostics.

####Buttons

Calling throttle.buttons.button_name() will return True if that button is currently pressed, and False if not.
Future documentation updates will include a table of defined buttons here, but for now, examine namedcontrollers.py and see where the buttons are listed in definition of the WarthogThrottle class.  

**Example:**
````python
diagnostics.watch(throttle.buttons.micswitch_push() )   #Shows 'True' or 'False' in the FreePIE Watch window
diagnostics.watch(throttle.buttons.autopilot_engage_disengage() )

````

Note that: 
1. It's perfectly possible for the same button to have multiple names
2. Some controls are listed as buttons but *also* as toggles.
3. You can define your own button names easily, without necessarily editing namedcontrollers.py - just subclass NamedController or one of its subclasses (you'll need to take care of calling parent initializers though)
4. Some buttons look like 'hats', but aren't implemented as a POV hat when you view them in joy.cpl.  For example, the Warthog Throttle's 'micswitch' (the hat that falls under the user's left thumb at the top) is actually buttons 2,3,4,5 and 6.  throttle.hats.hat_name() is only for 'real' hats.  I'm planning a better abstraction for this in a future update.


####Toggles

Calling throttle.toggles.toggle_name() will return a string that represents the current state of that switch.

**Example:**
````python
diagnostics.watch(throttle.toggles.eac() ) # Shows 'ARM' or 'OFF' in the FreePIE Watch window
diagnostics.watch(throttle.toggles.flaps() ) # Shows 'UP', 'M/R' or 'DN'
````

The key benefit of using the .toggles is that a result is given even when the underlying button is not pressed.  For example, if you were monitoring the Flaps switch using vanilla FreePIE, you would get the values like this:

````python
if joystick[1].getDown(21):
  #flaps switch is up
  
if joystick[1].getDown(22):
  #flaps switch is down
````

You could test for 'flaps switch is in the middle' by combining these, but the point is there is no specific event fired when the flaps switch (or any other toggle) is in its 'normally off' position.  Contrast that with throttle.toggles.toggle_name() that always returns a value.

**State Names**

By default if you call throttle.toggles.toggle_name(), the string that is returned will be the text that is physically printed on the stick next to that toggle position.  For example, if you call throttle.toggles.engine_left_fuel() , you will get either "NORM" or 'OVERRIDE".  

It is envisaged that some Warthog users will replace their top-plates with custom ones (perhaps like the user in [this thread at the Star Citizen Forums](https://forums.robertsspaceindustries.com/discussion/233435/custom-sc-warthog-throttle-plates-prototype/p1) ) and won't be easily able to see the original text.  Therefore, I've created a mechanism to get a 'simpler' version of the toggle state name.  If you call throttle.toggles.toggle_name(1), you will get a result like UP or DOWN instead of NRM or DIS.

**Example**:

````python
if throttle.toggles.apu() == 'START':
  #do something
  
if thottle.toggles.apu(1) == 'UP':
  #equivalent to the above
````

**Implementation Detail**

The toggles are configured (by me, you shouldn't have to change this)  in the class definition, which looks like this:

````python
class WarthogThrottle(NamedController):
  buttons={
    #...
  }
  
  toggles={
    'apu': {0: ['OFF','DOWN']  ,  20: ['START','UP;] }
    #...
    }
````

When you call thottle.toggles.apu() , the system examines this definition, and tests whether button index 20 is pressed or not.  If it is, it returns the first item  in the list of strings for that button - ['START','UP'], so in this case it will return 'START'.

If you call throttle.toggles.apu(1), it will instead return the *second* item (item index 1 in the list), which is 'UP'.

####Axes

####Hats
  


