if starting:
	
	import namedcontrollers
	
	throttleID=2 #probably different for you
	stickID=3
				
	throttle = namedcontrollers.WarthogThrottle(joystick[throttleID])
	stick = namedcontrollers.WarthogStick(joystick[stickID])

diagnostics.watch(throttle.toggles.apu() )
diagnostics.watch(throttle.toggles.eac() )
diagnostics.watch(throttle.toggles.eng_fuel_l() )
diagnostics.watch(throttle.toggles.engine_right_oper() )
diagnostics.watch(throttle.toggles.flaps() )

diagnostics.watch(throttle.axes.left() )
diagnostics.watch(throttle.axes.slider() )

diagnostics.watch(throttle.hats.coolie() )
diagnostics.watch(throttle.hats.coolie.getRawValue() )

diagnostics.watch(throttle.hats.mic() )
diagnostics.watch(throttle.hats.mic.getRawValue() )

if stick.buttons.trigger():
	keyboard.setPressed(Key.F)

if stick.buttons.thumbtrigger.activatedOnce():
	keyboard.setPressed(Key.G)

#you can access FreePIE's view of the controller as well:
diagnostics.watch(throttle.controller.getDown(1) )

diagnostics.watch(throttle.buttons.autopilot() )

diagnostics.watch(throttle.buttons.autopilot.getTimeSinceLastStateChange() )
diagnostics.watch(throttle.buttons.autopilot.getTimeSinceLastPress() )
diagnostics.watch(throttle.buttons.autopilot.getTimeSinceLastRelease() )

diagnostics.watch(throttle.buttons.autopilot.getDurationOfMostRecentPressedState() )
diagnostics.watch(throttle.buttons.autopilot.getDurationOfMostRecentReleasedState() )
diagnostics.watch(throttle.buttons.autopilot.getTimeSinceLastPress() )

diagnostics.watch(throttle.buttons.autopilot.pressedFor(3) )
diagnostics.watch(throttle.buttons.autopilot.heldFor(10) )





diagnostics.watch(throttle.buttons.eac() )
diagnostics.watch(throttle.buttons.eac.getTimeSinceLastStateChange() )
diagnostics.watch(throttle.buttons.eac.getLog())
diagnostics.watch(throttle.buttons.eac.getPressesLog() )
diagnostics.watch(throttle.buttons.eac.getReleasesLog() )


#TODO include all named buttons and toggles here for completeness
