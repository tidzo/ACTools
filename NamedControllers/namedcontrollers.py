import functools
import sys

class MockController(object):
	def getDown(self, id):
		return 'fish %s' % id
		
	def getPressed(self, id):
		return 'finger %s' % id
	
		
class NamedController(object):

	#This maps plural, 'friendly' class names to real class names
	controlTypesMap={'buttons':'NamedButton', 'toggles':'NamedToggle', 'axes':'NamedAxis', 'hats':'NamedHat' }
	
	
	
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

	def getValue(self):
		return self.controller.getDown(self.zeroIndexedButtonID)

	def __call__(self):
		return self.getValue()
		
		


class NamedToggle(NamedControl):
	friendlyClassName='toggle'
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
		
	def getState(self,namingStrategy=''):
		if namingStrategy == '':
			namingStrategy=self.defaultNamingStrategy
			namingIndex=self.defaultNamingIndex
		else:
			namingIndex=self.namingStrategies[namingStrategy.upper()]
		
		for friendlyButtonID in sorted(self.definition.keys(), reverse=True):
			if friendlyButtonID!=0:
				zeroIndexedButtonID=friendlyButtonID-1
				if self.controller.getDown(zeroIndexedButtonID):
					return self.definition[friendlyButtonID][namingIndex]
					
			else:
				#if we've reached 0, none of the buttons defined as possible states for this toggle were pushed, so we can return the 'unpushed' state name
				return self.definition[0][namingIndex]
	
	def getValue(self,namingStrategy=''):
		return self.getState(namingStrategy)
		
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
		


class NamedHat(NamedControl):
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
			
	    'coolie': 	
			{
			 'index': 0,
			 'positions':

				#left and right are from perspective of user operating this hat with their left index finger
				{-1: 'off', 0: 'up', 4500: 'up_and_right', 9000: 'right', 13500: 'down_and_right', 18000: 'down',
				 22500:'down_and_left', 27000:'left', 31500:'up_and_left'}
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
