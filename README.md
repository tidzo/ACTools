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

if throttle.toggles.eac()=='ARM' and throttle.toggles.rdr()=='NRM' and throttle.buttons.autopilot():
  
  #eject
  keyboard.setPressed(Key.LeftAlt)
  keyboard.setPressed(Key.L)
```

(If the 'EAC' toggle switch is set to 'ARM' (up), AND the 'RDR' toggle switch is set to 'NRM' (up), AND the 'Autopilot engage/disengage button is pressed, then emulate pressng LeftAlt plus L (the default eject key in [Star Citizen](https://robertsspaceindustries.com/enlist?referral=STAR-DLML-6LDN) (*referral link*) )

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

**Once vs Continuous Presses**

throttle.buttons.button_name() is exactly equivalent to joystick[id].getDown(id_number_of_that_button).  This means that it will return True continuously while the button is pressed.  Sometimes that is what you want, and sometimes it isn't.
FreePIE provides a .getPressed() method which will return True exactly once for each specific press of the button.  The NamedControls extensions lets you access this method conveniently as controller.buttons.button_name.getPressed() and, because
I thought 'pressed' was potentially ambiguous (is it pressed now, or was it pressed then, or...?), I also defined an alias of 'activatedOnce() for getPressed(), and 'activatedNow()' for 'getDown()'.  
This also helps for readabilty, for example if you have a switch like 'hat1_up' - hat1_up.activatedNow() is less confuising than hat1_up.getDown()!

````python
#These are identical - returning True only once for each button press:
stick.buttons.thumbtrigger.getPressed()
stick.buttons.thumbtrigger.activatedOnce()
joystick[id_of_that_controller].getPressed(id_number_of_that_button)

#and these are identical - returning True continuously while the button is held down:
stick.buttons.thumbtrigger()
stick.buttons.thumbtrigger.getDown()
stick.buttons.thumbtrigger.down()
stick.buttons.thumbtrigger.activatedNow()

#usage example:

#send keypress of letter f as long as joystick main trigger is held down
if stick.buttons.trigger():		
	keyboard.setPressed(Key.F)

#send one single keypress of the letter g for each press and release of the thumb trigger 
#(the big red button on top of warthog stick)
if stick.buttons.thumbtrigger.activatedOnce():
	keyboard.setPressed(Key.G)

````

**Timing of Presses**

Some basic work has been done on exposing the length of time that a button is pressed, held or released.  This needs significant work (not least with better naming) but as a taster of what is to come, the following will work so far:

````python
stick.buttons.trigger.getTimeSinceLastStateChange() #eg 5.145232457
stick.buttons.trigger.getTimeSinceLastPress()		
stick.buttons.trigger.getTimeSinceLastRelease()
stick.buttons.trigger.getDurationOfMostRecentPressedState()
stick.buttons.trigger.getDurationOfMostRecentReleasedState()

stick.buttons.trigger.pressedFor(3) 	# returns True if the most recent press was for 3 seconds or more 
										# (and the button is NOT currently pressed)
										
stick.buttons.trigger.heldFor(5) 		# returns True if the most recent press was for 3 seconds or more 
										#(and the button IS not currently pressed)
````

Future work will expand, clarify and rename these facilities, and perhaps eventually expand them to cover toggles and hat switches.


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

You could test for 'flaps switch is in the middle' by combining these, but the point is there is no specific event fired when the flaps switch (or any other toggle) is in its 'normally off' position.  Contrast that with throttle.toggles.toggle_name() that always returns a value.  So the NamedControllers equivalent to the above would be:

````python
if throttle.toggles.flaps()=='UP':
  #flaps switch is up
  
if throttle.toggles.flaps()=='M/R':
  #flaps switch is in the middle
  
if throttle.toggles.flaps()=='DN':
  #flaps switch is down
````  

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

If you call throttle.toggles.apu(1), it will instead return the *second* item (item index 1 in the list), which is 'UP'.  A future update will include a mechanism to specify which item in the lists should be the default when you instantiate the controller.

####Axes

throttle.axes.left() will return the current value of the left-hand side of the throttle pair.  Similarly .right() for the other side, and the mouse nub is available as .x() and .y() (and also under the aliases slew_x() and scx() ).

Some controls look like an axis but are in fact implemented as a 'slider'.  These controls might look different in joy.cpl.  They are available in FreePIE as joystick[id].sliders[slider_id],
but in this extension they work just like the other axes.  The slider on the right hand side of the Warthog throttle is accessible as throttle.axes.slider() - but the word slider there is just because that's what I've named it
in the definition of the WarthogThrottle class, not because it's 'a slider', if you see what I mean!


####Hats

throttle.hats.hat_name() will return a string representation of the current position of the specified POV hat, as a direction such as "up" or "down_and_left".  
Note that this only works for controls that appear as a hat in joy.cpl - 
in the case of the Warthog, both the stick and throttle have several 'hat' type controls which are not mapped in this way, and they will (currently) not be accessible under this .hats.hat_name() interface.  (That could be added easily in future)


###Configuration
A full configuration guide will be available soon, but in the mean time it should be easy to infer how controls are mapped by examining the static class definitions of NamedController, WarthogStick and WarthogThrottle in namedcontrollers.py.

  


