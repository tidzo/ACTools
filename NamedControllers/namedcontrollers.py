import functools
import sys
import collections
import time

clockstart=time.clock()

class MockController(object):
	def getDown(self, id):
		return 'fish %s' % id
		
	def getPressed(self, id):
		return 'finger %s' % id
	
		
class NamedController(object):

	#This maps plural, 'friendly' class names to real class names
	controlTypesMap={'buttons':'NamedButton', 'toggles':'NamedToggle', 'axes':'NamedAxis', 'hats':'HatFactory' }
	
	
	
	def __init__(self,controller=None):
		
		self.controller=controller
					
		self.defined_controls={'buttons':self.buttons, 'toggle':self.toggles, 'axis':self.axes, 'hat':self.hats }				

		#currently, the static class variables like .buttons and .toggles will have been populated into the object, containing the definitions of those controls.
		
		#for each controlType, we're going to create a ControlFactory object, which will create/find/store the actual Controls of that type, and  hold the definitions,
		#and that Factory will live at self.buttons, self.toggles etc, instead of the definitions that were there previously
		
		for controlType,className in self.controlTypesMap.iteritems():
			self.__dict__[controlType] = ControlFactory(parent=self, controlType=controlType, controlTypeDefinition=getattr(self,controlType), targetClassName=className )
		
			

class ControlFactory(object):
	
	def __init__(self,parent=None, controlType='', controlTypeDefinition='', targetClassName='',):
		self.parent=parent #the NamedController object (not the FreePIE controller object, which incidentally would be parent.controller)
		self.controlType=controlType #eg 'buttons'
		self.controlTypeDefinition=controlTypeDefinition #the definition for each controlType, as defined statically in the class itself
		self.targetClassName=targetClassName #eg 'NamedButton'
		
		
	def __getattr__(self,name):

		newControlClass = globals()[self.targetClassName]
		#create the new control, setting its 'parent' attribute to be the same as this Factory's parent, ie the controller, and passing just the definition of this control into its constructor
		
		newControl = newControlClass(parent=self.parent, controller=self.parent.controller, controlType=self.controlType, definition=self.controlTypeDefinition[name], name=name)
		
		#Store the new control in self.<controlname> so that it only gets created once.
		self.__dict__[name]=newControl
		
		return newControl

class HatFactory(object):

	#note this is __new__ and not __init__
	def __new__(self,parent=None,controller=None, controlType='', definition='', name='',):
		if definition['type'].upper()=='POV':
			return NamedPOVHat(parent=parent, controller=controller, controlType=controlType, definition=definition, name=name)
		else:
			#the 'positions' item in the button hat's definition is equivalent to a NamedToggle's definition, so we send that and use the same (subclassed) code to make the Control object.
			positionsDefinition=definition['positions']
			return NamedButtonHat(parent=parent, controller=controller, controlType=controlType, definition=positionsDefinition, name=name)

			
class NamedControl(object):
	def __init__(self,parent=None,controller=None, controlType='', definition='', name='',):
		self.parent=parent
		self.controller=controller 	#note that controller will usually be exactly the same as parent.controller, but this allows for some future flexibility
		self.controlType=controlType #eg 'buttons'
		self.definition=definition
		self.name=name

	
class NamedButton(NamedControl):
	friendlyClassName='button'
	def __init__(self,parent=None,controller=None,controlType='', definition='',name='',):
		self.parent=parent
		self.controller=controller
		self.controlType=controlType
		self.definition=definition
		self.name=name
		
		#FIXME trap button name not found
		self.friendlyButtonID=self.definition
		
		#FIXME trap negative number
		self.zeroIndexedButtonID=self.friendlyButtonID - 1
		
		
		self.getPressed=functools.partial(controller.getPressed,self.zeroIndexedButtonID)
		self.activatedOnce=self.getPressed
		
		self.getDown=functools.partial(controller.getDown,self.zeroIndexedButtonID)
		self.down=self.getDown
		self.activatedNow=self.getDown
		
		#populate the initial value of the button
		self.durationOfMostRecentPressedState=0
		self.durationOfMostRecentReleasedState=0
		self.duration=0
		self.timePressed=0
		self.timeReleased=0
		self.timeStateChanged=0
		
		logLength=20 #how many press/release timing data items to keep in the history
		historyLength=20 #how many press/release timing data items to keep in the history
		
		self.log=collections.deque(maxlen=logLength)
		self.history=collections.deque(maxlen=historyLength)
		self.pressDurationsLog=collections.deque(maxlen=logLength)
		self.releaseDurationsLog=collections.deque(maxlen=logLength)
		self.morseLog=collections.deque(maxlen=logLength)
		
		self.timeNow=time.clock()
		self.downPreviously=self.controller.getDown(self.zeroIndexedButtonID)
		downNow=self.downPreviously
		
		self.dashDuration=0.5
		
		
		if downNow:
			#button is held down at time of object initialisation
			self.timePressed=self.timeNow
		else:
			self.timeReleased=self.timeNow
		

		
		
	def _getRawCurrentValue(self):
		return self.controller.getDown(self.zeroIndexedButtonID)
	
	def getTimeInCurrentState(self):
		currentValue=self._getRawCurrentValue()
		if currentValue == self.lastValue:
			pass
		
			
		
	def getValue(self):
		downNow=self._getRawCurrentValue()
		timeNow=time.clock()
		
		if downNow and self.downPreviously:
			#STILL_PRESSED
			pass
				
		if downNow and not self.downPreviously:
			#JUST_PRESSED
			self._onPressed(timeNow)
			
		if not downNow and self.downPreviously:
			#JUST_RELEASED
			self._onReleased(timeNow)
			
		if not downNow and self.downPreviously==False:
			#STILL_RELEASED
			pass
						
		self.downPreviously=downNow
		
		return downNow

		
	def _writeToLog(self,event='',time=0.0):	#event=PRESS | RELEASE
		if event.upper().startswith('P'):
			eventCode=1
		else:
			eventCode=0
		self.log.append( (eventCode, time) )
		
	def _writeToHistory(self, event='', duration=0.0 ):
		if event.upper().startswith('P'):
			eventCode=1
			self.pressDurationsLog.append(duration)
		else:
			eventCode=0
			self.releaseDurationsLog.append(duration)
		self.history.append( (eventCode, duration) )
		
	def _writeToMorseLog(self,duration=0.0):
		if duration>self.dashDuration:
			self.morseLog.append('-')
		else:
			self.morseLog.append('.')
			
	def printMorseLog(self):
		result=''
		for i in range(0, len(self.morseLog)):
			result+=self.morseLog[i]
			
		return result
			
					
	def checkMorseLog(self,message):
		messageLength=len(message)
		if messageLength>len(self.morseLog):
			return False
			
		for i in range(0,messageLength):
			index=messageLength-i
			if message[i] != self.morseLog[0-index]:
				return False
				
		return True
			
		
		
	def _onPressed(self,timeNow):
		self.timePressed=timeNow
		self.timeStateChanged=timeNow
		self.durationOfMostRecentReleasedState=timeNow-self.timeReleased
		self._writeToLog('PRESS',timeNow)
		self._writeToHistory('RELEASED',self.durationOfMostRecentReleasedState)
		
		
	def _onReleased(self,timeNow):
		self.timeReleased=timeNow
		self.timeStateChanged=timeNow
		self.durationOfMostRecentPressedState=timeNow-self.timePressed
		self._writeToLog('RELEASED',timeNow)
		self._writeToHistory('PRESS',self.durationOfMostRecentPressedState)
		self._writeToMorseLog(self.durationOfMostRecentPressedState)
		
	def getLog(self):
		return self.log
		
	def getHistory(self):
		return self.history
		
	def getPressesLog(self):
		if len(self.pressDurationsLog)>0:
			return self.pressDurationsLog[-1]
		else:
			return False

	def getReleasesLog(self):
		if len(self.releaseDurationsLog)>0:
			return self.releaseDurationsLog[-1]
		else:
			return False
	
	def getTimeSinceLastStateChange(self):
		timeNow=time.clock()
		timeSinceLastStateChange=timeNow-self.timeStateChanged
		
		return timeSinceLastStateChange
	
	def getTimeSinceLastPress(self):
		timeNow=time.clock()
		timeSinceLastPress=timeNow-self.timePressed
		return timeSinceLastPress
		
	def getTimeSinceLastRelease(self):
		timeNow=time.clock()
		timeSinceLastRelease=timeNow-self.timeReleased
		return timeSinceLastRelease
		
	
	def getDurationOfMostRecentPressedState(self):
		return self.durationOfMostRecentPressedState
		
	def getDurationOfMostRecentReleasedState(self):
		return self.durationOfMostRecentReleasedState
		
	def pressedFor(self,duration):
		if self._getRawCurrentValue()==False and self.getDurationOfMostRecentPressedState() > duration:
			return True
		else:
			return False
			
	def heldFor(self,duration):
		if self._getRawCurrentValue()==True and self.getTimeSinceLastStateChange() > duration:
			return True
		else:
			return False
	
	
	
	def __call__(self):
		return self.getValue()
		
		


class NamedButtonGroup(NamedControl):
	friendlyClassName='buttongroup'
	def __init__(self,parent=None,controller=None,controlType='', definition='', name='',):
		self.parent=parent
		self.controller=controller
		self.controlType=controlType
		self.definition=definition
		self.name=name
		
		self.namingStrategies={'SIMPLE':0, 'AUTHENTIC':1}
		self.defaultNamingStrategy='SIMPLE'
		self.defaultNamingIndex=self.namingStrategies[self.defaultNamingStrategy]
		
		
		#FIXME trap button name not found

	def getRawValue(self):
		
		for friendlyButtonID in sorted(self.definition.keys(), reverse=True):
			if friendlyButtonID!=0:
				zeroIndexedButtonID=friendlyButtonID-1
				if self.controller.getDown(zeroIndexedButtonID):
					return friendlyButtonID
						
			else:
				#if we've reached 0, none of the buttons defined as possible states for this toggle were pushed, so we can return the 'unpushed' state name
				return 0
	
	
	def getValue(self,namingStrategy=''):
		if namingStrategy == '':
			namingStrategy=self.defaultNamingStrategy
			namingIndex=self.defaultNamingIndex
		else:
			namingIndex=self.namingStrategies[namingStrategy.upper()]

		friendlyButtonID = self.getRawValue()
		
		possibleReturnValues=self.definition[friendlyButtonID]
		if isinstance(possibleReturnValues,list):
				
			#FIXME check namingIndex is valid
			return possibleReturnValues[namingIndex]
		else:
			#if not a list, just return the value.
			return possibleReturnValues
						
					
	def __call__(self,namingStrategy=''):
		return self.getValue(namingStrategy)

		
	
		
class NamedAxis(NamedControl):

	friendlyClassName='axis'
	
	def __init__(self,parent=None,controller=None, controlType='', definition='',name='',):
		self.parent=parent
		self.controller=controller
		self.controlType=controlType
		self.definition=definition
		self.name=name
		
		#some controls that a user might consider to be an axis are in fact a 'slider'.  
		#The NamedAxis class tries to abstract that away but needs to know which we're dealing with so as to be able to get the value of the 'axis' either way.
		#If the definition maps the 'axis' name to a string, delegate to controller.<axisname>  and if it maps to an int, delegate to controller.sliders[<sliderIndex>]
		
		if isinstance(self.definition,int):
			self.slider=True
			self.sliderIndex = self.definition
		else:
			self.axisInternalName = self.definition
			self.slider=False
			
	def getValue(self):
		if self.slider:
			return self.controller.sliders[self.sliderIndex]
		else:
			return getattr(self.controller,self.axisInternalName)
		
	
	def __call__(self):
		return self.getValue()
		

class NamedPOVHat(NamedControl):
	friendlyClassName='hat'
	def __init__(self,parent=None,controller=None, controlType='', definition='', name='',):
		self.parent=parent
		self.controller=controller
		self.controlType=controlType
		self.definition=definition
		self.name=name
		
		self.index=self.definition['index']

	def getRawValue(self):
		return self.controller.pov[self.index]
		
	def getValue(self):
		rawValue=self.getRawValue()
		namedValue=self.definition["positions"][rawValue]
		return namedValue
		
	def __call__(self):
		return self.getValue()


#Toggles and ButtonHats are subclases of a NamedButtonGroup. 
#I might add extra features in future such as tracking changes over time - this is where they would be implemented
class NamedToggle(NamedButtonGroup):
	friendlyClassName='toggle'
			
		
#Hat switches are often implemented as a group of buttons of which only one can be pressed, 
#rather than a degree-based hat control	- that is best represented as a ButtonGroup
class NamedButtonHat(NamedButtonGroup):
	friendlyClassName='hat'
		

class WarthogThrottle(NamedController):
	buttons={
		'slew_push': 1,
		
		'micswitch_push':2,
		'micswitch_up':3,
		'micswitch_forwards':4,
		'micswitch_down':5,
		'micswitch_back':6,
		'speedbrake_forward':7,
		'speedbrake_back':8,

		'boatswitch_forward':9,
		'boatswitch_back':10,

		'china_forward': 11,
		'china_back':12,

		'pinky_forward': 13,
		'pinky_back': 14,

		'left_throttle_button': 15,

		'eng_fuel_left_up': 16,
		'eng_fuel_right_up': 17,

		'eng_oper_left_down': 18,
		'eng_oper_right_down': 19,
		
		'engine_fuel_left_up': 16,
		'engine_fuel_right_up': 17,

		'engine_oper_left_down': 18,
		'engine_oper_right_down': 19,

		'apu': 20, 'apu_start': 20,

		'lgwarn':21,

		'flaps_up': 22,
		'flaps_down': 23,

		'eac': 24,
		'rdr': 25,

		'autopilot': 26,
		'autopilot_engage_disengage': 26,
		'autopilot_path': 27,
		'autopilot_alt': 28,

		'left_throttle_idle': 29,
		'right_throttle_idle': 30,

		'engine_oper_left_up': 31,
		'engine_oper_right_up': 32,
	
	}

	toggles={
						
		'speedbrake': {0:['MID','MIDDLE'],7:['FRONT','FORWARDS'], 8:['BACK','BACKWARD']},

		'boatswitch': {0:['MID','MIDDLE'],9:['FRONT','FORWARDS'], 10:['BACK','BACKWARD']},

		'china': {0:['MID','MIDDLE'],11:['FRONT','FORWARDS'], 12:['BACK','BACKWARD']},

		'apu': {0:['OFF','DOWN'],20:['START','UP']},
		'flaps': {0: ['MVR','MIDDLE'], 22:['UP','UP'], 23:['DN','DOWN']},
		'eac': {0:['OFF','DOWN'],24:['ARM','UP']},
		'rdraltm': {0:['DIS','DOWN'],25:['NRM','UP']},
		'autopilotmode': {0:['ALT/HDG','MIDDLE'],27:['PATH','UP'],28:['ALT','DOWN']},
		
		'eng_oper_l': {0:['NORM','MIDDLE'], 18:['MOTOR','DOWN'], 31:['IGN','UP']},
		'eng_oper_r': {0:['NORM','MIDDLE'], 19:['MOTOR','DOWN'], 32:['IGN','UP']},
		'eng_fuel_l': {0:['OVERRIDE','DOWN'], 16:['NORM','UP'], },
		'eng_fuel_r': {0:['OVERRIDE','DOWN'], 17:['NORM','UP'], },
		
		'engine_oper_l': {0:['NORM','MIDDLE'], 18:['MOTOR','DOWN'], 31:['IGN','UP']},
		'engine_oper_r': {0:['NORM','MIDDLE'], 19:['MOTOR','DOWN'], 32:['IGN','UP']},
		'engine_fuel_l': {0:['OVERRIDE','DOWN'], 16:['NORM','UP'], },
		'engine_fuel_r': {0:['OVERRIDE','DOWN'], 17:['NORM','UP'], },
		
		'engine_left_oper': {0:['NORM','MIDDLE'], 18:['MOTOR','DOWN'], 31:['IGN','UP']},
		'engine_right_oper': {0:['NORM','MIDDLE'], 19:['MOTOR','DOWN'], 32:['IGN','UP']},
		'engine_left_fuel': {0:['OVERRIDE','DOWN'], 16:['NORM','UP'], },
		'engine_right_fuel': {0:['OVERRIDE','DOWN'], 17:['NORM','UP'], },
		
		
		
		
		'pinky': {0:['MID','MIDDLE'], 13:['FRONT','FORWARD'], 14:['BACK','BACKWARD'] },  
		'left_throttle': {0:['ACTIVE','ACTIVE'],30:['IDLE','IDLE']},                            
		'right_throttle': {0:['ACTIVE','ACTIVE'],29:['IDLE','IDLE']},                            
	
	}
				
		
	axes={
		'left':'zRotation',
		'right':'z',
		'slew_x':'x',
		'slew_y':'y',
		'scx': 'x',
		'scy': 'y',
		'x': 'x',
		'y': 'y',
		'slider': 0, #use an integer to refer to a slider as an 'axis'
	}
		
	hats={
			
		
		'coolie':{
			 'type': 'POV',
			 'index': 0,
			  
			 #left and right are from perspective of user operating this hat with their left index finger
			 'positions': {
				-1: 	'OFF',
				 0: 	'UP',
				 4500: 	'UP_AND_RIGHT',
				 9000:  'RIGHT',
				13500:  'DOWN_AND_RIGHT',
				18000:  'DOWN',
				22500:  'DOWN_AND_LEFT',
				27000:  'LEFT',
				31500:  'UP_AND_LEFT',
			 }
			},
			
		'mic': {
			'type': 'BUTTONS',
			'positions' :{
				0: 'OFF', 
				2: 'PUSHED',
				3: 'UP',
				4: 'FORWARDS',
				5: 'DOWN',
				6: 'BACKWARDS'
			},
		},
		'china':{
			'type': 'BUTTONS',
			'positions': {
				0: 'MIDDLE',
				11: 'FORWARDS',
				12: 'BACKWARDS',
				},
		
			
			}
		}
	



		
class WarthogStick(NamedController):

	buttons={
		'tg1':1,
		'guntrigger1':1,
		'trigger':1,
		'trigger1':1,
		'tg2':6,
		'trigger2':6,
		'guntrigger2':6,
		
		#no problem having multiple names for same button
		'thumbtrigger':2,
		'thumbfire':2,
		's2':2,
		'weaponsrelease':2,
		'nsb':3,
		'nosewheel_steering_button':3,
		'nosewheel':3,
		's3':3,
		's4':4,
		'pinkie_lever':4,
		'pinkie':4,
		'leveer':4,
		'master_mode_control_button':5,
		'mmcb':5,
		'mode':5,
		's1':5,

		
		'h2u':7,
		'h2r':8,
		'h2d':9,
		'h2l':10,

		'hat2up':7,
		'hat2right':8,
		'hat2down':9,
		'hat2left':10,

		'tms_up':7,
		'tms_right':8,
		'tms_down':9,
		'tms_left':10,


		'h3u':11,
		'h3r':12,
		'h3d':13,
		'h3l':14,

		'hat3up':11,
		'hat3right':12,
		'hat3down':13,
		'hat3left':14,
	
		'dms_up':11,
		'dms_right':12,
		'dms_down':13,
		'dms_left':14,

		
		'h4u':15,
		'h4r':16,
		'h4d':17,
		'h4l':18,
		'h4p':19,

		'hat4up':15,
		'hat4right':16,
		'hat4down':17,
		'hat4left':18,
		'hat4push':19,
	
		'cms_up':15,
		'cms_right':16,
		'cms_down':17,
		'cms_left':18,
		'cms_push':19,
			
	}
		
	axes={
		'x':{'axis':'x'},
		'y':{'axis':'y'},
	}
	
	toggles={}
	hats={}
