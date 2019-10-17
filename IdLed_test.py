import os, sys, time		#, shutil, re
import telnetlib, getopt	#, socket, datetime
import traceback
#from robot.libraries.BuiltIn import BuiltIn

BC_IpAddress_map = []
Powerbay_Number_map = []
Sled_Bit_map = []

NumberOfBC = 0
Number_of_Powerbay = 0

IdLed_log, current_dir, subdir = ['','','']
ABSENT_MSG = "Requested target is not present!"
JBOD_MSG = "This operation is not supported for JBOD sled!"
INVALID_MSG = "Invalid target address!"
BUSY_MSG = "Network busy. Please try again later!"
CONTROLLER_BUSY = "Controller busy. Please try again later!"
#################################################################################################################
####################################Steps followed for this test script##########################################
#################################################################################################################
#1.  login to MC and get info of rack.
#2.  if login and acquired info is correct start test cycle.
#3.  individualy set IdLed "ON" on every target which is supported and check result of IdLed state after 5 sec.
#4.  In some rare case if IdLed not give expected("ON/OFF") result then we need to do retry 8 times with 2 sec.
#5.  Total after 20 sec if we still not get expected("ON/OFF") result we will consider it as a failure state.
#6.  During IdLed set CLI response is like,
# 											"Requested target is not present!" , 
#											"This operation is not supported for JBOD sled!" , 
#											"Invalid target address!", 
#											"Network busy. Please try again later!",
# 											"Controller busy. Please try again later!".  
#7.  Any CLI response from step 6 occured during set IdLed then it will be consider as a 'PASS' result.
#8.  All above steps will be repeat for set IdLed "OFF" process.
#9.  After completed individual "ON/OFF" then script will move for star support for IdLed "ON/OFF" and it will execute on different targets which mentioned in step 10.
#10. Different targets like, Rack*/Powerbay*/mc1, Rack*/Block*/BC, Rack*/block*/sled* ,Rack*/powerbay*/im and Rack*/Block*/sled*/Node1.
#11. if we find any fail case in response we repeat step number 4 and 5.
#12. if all cases and loops result is pass then test case consider as a pass.

# NOTE: Fail case is actually opposite of current execution process. For example : if IdLed "ON" process is in execution then fail case will be "OFF" and vice versa. 
#################################################################################################################

dict_cmd = {'BC_star': 'Rack*/Block*/BC',
			'IM_star': 'Rack*/PowerBay*/IM',
			'MC_star': 'Rack*/Powerbay*/MC1',
			'Node_star': 'Rack*/block*/sled*/node1',
			'Sled_star': 'Rack*/Block*/Sled*',
			'MC' : 'Rack1/Powerbay%s/MC1',
			'BC' : 'Rack1/Block%s/BC',
			'IM' : 'Rack1/PowerBay1/IM',
			'Sled' : 'Rack1/Block%s/Sled%s'}

#################################################################################################################

class IdLed_test:
	def __init__(self):
		self.tn = None
		self.status = None
		self.user = 'root'
		self.password = 'calvin'
		#~ self.log_file = 'IdLed_test.log'
		timestr = time.strftime("%Y%m%d-%H%M%S")
		file_name = "IdLed_test_" + timestr + ".log"
		self.log_file = file_name
		self.loop = '1'
		self.debug_mode = 'yes'
		self.HOST_IP = ''

#################################################################################################################
	def execute_cmd(self, cmd, time_out=120, expect='Exit the Session'):
		try:
			self.tn.write('CLI\n')
			self.tn.write(cmd)
			self.tn.write('exit\n')
			return self.tn.read_until(expect, time_out)
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname, lineno, fn, text = frame
				print self.logging(
					"Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
#################################################################################################################
	def id_led_test(self, property_Value, target, target_number = 0, sled_number = 0):
		iRet = 'PASS'
		if(target_number != 0):
			if(sled_number != 0):
				target_buf = dict_cmd[target] % (target_number,sled_number)
			else:
				target_buf = dict_cmd[target] % target_number 
		else:
			target_buf = dict_cmd[target]

		try:
			if property_Value == 'OFF':
				msg = "Set the properties \"IdLedState\" to \"OFF\" successfully!"
				FAIL_CASE = "ON"
			else:
				msg = "Set the properties \"IdLedState\" to \"ON\" successfully!"
				FAIL_CASE = "OFF"

			self.login_to_MC()
			print self.logging("Current time :%s" % (time.ctime()))
			Response_buf = self.execute_cmd("set %s IdLedState=%s\n" % (target_buf, property_Value))
			if msg in Response_buf:
				time.sleep(3)
				Response_buf = self.execute_cmd("show -d Properties=IdLedState %s\n" % (target_buf))
				if FAIL_CASE in Response_buf:
					Retry_Count = 8
					while (Retry_Count):
						print self.logging("Response_buf = %s " % (Response_buf))
						print self.logging("waiting more 2 sec for MC thread sync")
						time.sleep(2)
						Response_buf = self.execute_cmd("show -d Properties=IdLedState %s\n" % (target_buf))
						if FAIL_CASE in Response_buf:
							Retry_Count -= 1
						else:
							break
					if (Retry_Count == 0):
						print self.logging(
							"Execute setIdLedState = %s command on %s    : IdLedState  : FAIL" % (
								target_buf, property_Value))
						iRet = 'FAIL'
				else:
					print self.logging("Response_buf = %s " % (Response_buf))
					print self.logging(
						"Execute setIdLedState = %s command on %s    : IdLedState : PASS" % (
							target_buf, property_Value))

			else:
				print self.logging("Response_buf = %s " % (Response_buf))
				if BUSY_MSG in Response_buf:
					print self.logging("Network busy")
				elif INVALID_MSG in Response_buf:
					print self.logging("Invalid  message")
				elif CONTROLLER_BUSY in Response_buf:
					print self.logging("Controller busy message")
				elif ABSENT_MSG in Response_buf:
					print self.logging("Absent  message")
				elif JBOD_MSG in Response_buf:
					print self.logging("JBOD  message")
				else:
					print self.logging(
						"Execute setIdLedState = %s command on %s                       : FAIL : Success message not found" % (
							target_buf, property_Value))
					iRet = 'FAIL'

			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname, lineno, fn, text = frame
				print self.logging(
					"Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
#################################################################################################################
	def usage(self):
		print "usage : python IdLed_test.py"
		print "Common OPTIONS:"
		print "               -h,               --help               -- show Usage, Options"
		print "               -u <user>,        --user=<usernm>      -- username of MC"
		print "               -p <passwd>,      --password=<passwd>  -- password of username"
		print "               -r <rhost>,       --rhost=<rhost>      -- MC IP"
		print "               -l <No.of Test>,  --loop=<No.of Test>  -- No. of test cycle"
		print "               -f <logfile>,     --file=<logfile>     -- Log filename"
		print "               -d <yes/no>,      --debug=<yes/no>     -- Debug mode"
#################################################################################################################
	def main(self,argv):
		try:
			if len(argv) == 0:
				self.usage()
				sys.exit()
			opts, args = getopt.getopt(argv, "h:r:u:p:f:l:d:", ["help","rhost=","user=","password=","file=","loop=","debug="])
		except getopt.GetoptError as err:
			print str(err)
			self.usage()
			sys.exit()

		for o, a in opts:
			if o in ("-h", "--help"):
				self.usage()
				sys.exit()
			elif o in ("-r", "--rhost"):
				self.HOST_IP = a
			elif o in ("-u", "--user"):
				self.user = a
			elif o in ("-p", "--password"):
				self.password = a
			elif o in ("-f", "--file"):
				self.log_file = a
			elif o in ("-l", "--loop"):
				self.loop = a	
			elif o in ("-d", "--debug"):
				self.debug_mode = a
			else:
				print 'wrong opt'
				self.usage()
				sys.exit()

		#if self.HOST_IP != '':
			#ret = True if os.system("ping -c 3 " + self.HOST_IP + " > /dev/null") is 0 else False
			#if ret == False:
				#print " MC is not present "
				#sys.exit()

			self.IdLedState_ON_OFF('','','')
#################################################################################################################
	def blockPrint(self):
		sys.stdout = open(os.devnull, 'w')
#################################################################################################################
	def check_ping(self):
		result = False
		flag = 0
		while result == False:

			# Mc_ping = pyping.ping(self.HOST_IP)
			result = True if os.system("ping -c 3 " + self.HOST_IP + " > /dev/null") is 0 else False
			if result == True:
				break
			else:
				print self.logging('\nUnable to reach ' + self.HOST_IP + '. Wait for 15 minute!')
				time.sleep(900)
				flag = 1
				continue
		if flag == 1:
			print self.logging("\nWait for 240 second for environment setup!")
			time.sleep(240)
		else:
			print self.logging("\nWait for 220 second for environment setup!")
			time.sleep(220)
			print self.logging("\nConnection success with system " + self.HOST_IP + ".\n")
#################################################################################################################
	def logging(self, my_string):
		global IdLed_log,current_dir,subdir
		try:
			filepath = os.path.join(current_dir, subdir, str(self.HOST_IP), IdLed_log)
			with open(filepath,'a+') as log_file:
				log_file.write(str(my_string))
				log_file.write("\n")
				log_file.close()
		except IOError as e:
			print "I/O error({0}): {1}".format(e.errno, e.strerror)
		except ValueError:
			print "Could not convert data to an string."
		except:
			print "Unexpected error:", sys.exc_info()[0]
			raise RuntimeError('logging init failed')
		return my_string
#################################################################################################################
	def create_log_folder(self,log_files):
		global IdLed_log,current_dir,subdir
		try:
			current_dir = os.path.dirname(os.path.realpath(__file__))
			subdir = "../logs"

			if not os.path.exists(current_dir+"/"+subdir):
				os.mkdir(os.path.join(current_dir, subdir))

			if not os.path.exists(current_dir+"/"+subdir+"/"+str(self.HOST_IP)):
				os.mkdir(os.path.join(current_dir, subdir,str(self.HOST_IP)))

			IdLed_log = log_files
			New_IdLed_log = current_dir + "/" + subdir + "/" + str(self.HOST_IP) + "/" + IdLed_log
			old_IdLed_log = New_IdLed_log+"_old"

			if os.path.exists(old_IdLed_log):
				os.remove(old_IdLed_log)

			if os.path.exists(New_IdLed_log):
				os.rename(New_IdLed_log,old_IdLed_log)

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('create_log_folder failed')
			return 'FAIL'
		else:
			print self.logging("\ncreate %s successfully"%(New_IdLed_log))
#################################################################################################################
	def login_to_MC(self):
		try:
			self.tn = telnetlib.Telnet(self.HOST_IP)

			self.tn.read_until("login: ")
			self.tn.write(self.user + "\n")

			self.tn.read_until("Password: ")
			self.tn.write(self.password + "\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('login_to_MC failed')
			return 'FAIL'
#################################################################################################################
	def login_to_MC_for_status(self):
		try:
			self.status = telnetlib.Telnet(self.HOST_IP)

			self.status.read_until("login: ")
			self.status.write(self.user + "\n")

			self.status.read_until("Password: ")
			self.status.write(self.password + "\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))	
				raise RuntimeError('login_to_MC_for_status failed')
			return 'FAIL'
#################################################################################################################
	def parse_response_property(self, tn_buf, property_name):
		operation_status = 'NA'
		try:
			tn_buf_ = str(tn_buf)
			for line in tn_buf_.splitlines():
				if str(property_name) in line:
					line = line.strip()
					
					if (line.split()[-1]) != '=':
						if "ON" or "OFF" or "BLINKING" in str(line):
							value = line.split(" ",2)[2]
							operation_status = value
					else:
						operation_status = 'NA'
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('parse_response_property failed')
		return operation_status
#################################################################################################################
	def get_BC_IpAddress(self):
		try:
			buf = self.execute_cmd('show -d properties=IpAddress Rack*/block*/BC\n',120)
			for line in buf.splitlines():
				if 'IpAddress = 10.253.' in line:
					value = line.split()[-1]
					value = value.split('.')[-1]
					if (value != "NA"):
						BC_IpAddress_map.append(value)
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_BC_IpAddress failed')
			return 'FAIL'
#################################################################################################################
	def Is_Jbod_sled(self,Sled_target):
		sled_presence = 'NA'
		try:
			Response_buf  = self.execute_cmd("show -d properties=SledType %s\n"%(Sled_target), 120)
			sled_presence = self.parse_response_property(Response_buf,'SledType = ')
			self.tn.write('exit\n')
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('Is_Jbod_sled failed')
			return 'FAIL'
#################################################################################################################
	def get_Powerbay_number(self):
		global Powerbay_Number_map
		PSU_Present='0'
		try:
			buf = self.execute_cmd('show -d properties=NumberOfPSU,PowerBayNumber Rack*/PowerBay*\n')
			for line in buf.splitlines():
				if 'NumberOfPSU = ' in line:
					if (line.split()[-1]) != '=':
						value = line.split("= ")[1]
						if 'NA' in value:
							continue
						PSU_Present='1'											# assign to actual PB only
					else:
						print self.logging("skip line: %s " % (line))

				if "PowerBayNumber = " in line:
					if (line.split()[-1]) != '=':
						powerbayno=line.split("= ")[1]
						if PSU_Present =='1':
							powerbayno = powerbayno.replace(' ', '')
							Powerbay_Number_map.append(powerbayno)
						PSU_Present='0'
					else:
						print self.logging("skip line: %s " % (line))
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Powerbay_number failed')
			return 'FAIL'
############################################################################################################
	def get_sled_bitmap_per_block(self,block_num):
		global Sled_Bit_map
		try:
			self.tn.write("CLI\n")
			self.tn.write('show -d properties=SledNumbers Rack*/Block'+block_num+'/BC\n')
			self.tn.write("exit\n")
			self.tn.write("exit\n")
			buf=self.tn.read_all()
			for line in buf.splitlines():
				if 'SledNumbers = ' in line:
					value = line.split()[-1]
					if (value != "NA" and value != "" and value != "="):
						Sled_Bit_map.append(value)
					else:
						Sled_Bit_map.append("NA")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))	
				raise RuntimeError('get_sled_bitmap_per_block failed')
				return 'FAIL'
#################################################################################################################

	def Execution_start_star(self, property_value):
		iRet_MC   = 'PASS'
		iRet_BC   = 'PASS'
		iRet_sled = 'PASS'
		iRet_IM   = 'PASS'
		iRet_Node = 'PASS'
		iRet      = 'PASS'
		global set_console_buffer

		try:
			iRet_MC = self.id_led_test(property_value, "MC_star")
				
			time.sleep(1)
			iRet_BC = self.id_led_test(property_value, "BC_star")

			time.sleep(1)
			iRet_sled = self.id_led_test(property_value, "Sled_star")
			
			time.sleep(1)
			iRet_IM = self.id_led_test(property_value, "IM_star")
				
			time.sleep(1)
			iRet_Node = self.id_led_test(property_value, "Node_star")
				
			time.sleep(1)
			self.tn.write("exit\n")
			set_console_buffer = self.tn.read_all()
			
			if iRet_MC != 'PASS' or iRet_BC != 'PASS' or iRet_IM != 'PASS' or iRet_sled != 'PASS' or iRet_Node != 'PASS':
				iRet = 'FAIL'
			
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('execute_command failed')
			
		return iRet

###########################################################################################################################################################
	def Execution_start(self, property_value):
		iRet = 'PASS'
		iRet_Final = 'PASS'
		global BC_IpAddress_map, set_console_buffer, NumberOfBC, Sled_Bit_map

		try:
			self.login_to_MC()
			for index in range(Number_of_Powerbay):
				iRet = self.id_led_test(property_value,"MC",Powerbay_Number_map[index])
				if iRet == 'FAIL':
					iRet_Final = 'FAIL'

			time.sleep(1)

			for index in range(NumberOfBC):
				iRet = self.id_led_test(property_value, "BC", BC_IpAddress_map[index])
				self.get_sled_bitmap_per_block(str(BC_IpAddress_map[index]))
				if iRet == 'FAIL':
					iRet_Final = 'FAIL'

			time.sleep(1)

			self.login_to_MC()
			for index in range(NumberOfBC):
				sled_list = str(Sled_Bit_map[index]).split(",")
				size = sled_list.__len__()
				for S in range(size):
					if sled_list[S] != 'NA' and sled_list[S] != 'N/A':
						Sled_target = "Rack1/Block" + BC_IpAddress_map[index] + "/Sled" + sled_list[S]
						if self.Is_Jbod_sled(Sled_target) == "JBOD":
							print self.logging("Execute setIdLedState = %s command on Rack1/Block%s/Sled%s                   : PASS : SledType = JBOD"%(property_value, BC_IpAddress_map[index], sled_list[S]))
						else:
							iRet = self.id_led_test(property_value, "Sled", BC_IpAddress_map[index], int(sled_list[S]))
							if iRet == 'FAIL':
								iRet_Final = 'FAIL'
			time.sleep(1)
			Response_buf = self.execute_cmd("show -d Properties=PresenceState Rack1/PowerBay1/IM\n")
			IM_PRESENT_STATE = self.parse_response_property(Response_buf,"PresenceState")
			print self.logging("IM_PRESENT_STATE = %s"%(IM_PRESENT_STATE))
			if IM_PRESENT_STATE == 'PRESENT':
				iRet = self.id_led_test(property_value, "IM")
				if iRet == 'FAIL':
					iRet_Final = 'FAIL'

			time.sleep(1)
			self.tn.write("exit\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('execute_command failed')
			
		return iRet_Final
#################################################################################################################
	def get_Rack_PowerState(self):
		start_stop_status = 'NA'
		try:
			self.login_to_MC_for_status()
			self.status.write("CLI\n")
			self.status.write("show -d properties=PowerState RACK1\n")
			self.status.write("exit\n")
			Response_buf = self.status.read_until('Exit the Session',120)
			self.status.write("exit\n")
			start_stop_status = self.parse_response_property(Response_buf,'PowerState = ')
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_LastPowerChangeStatus failed')
		return start_stop_status
#################################################################################################################
	def get_FW_Version(self,Target):
		fw_version = 'NA'
		try:
			self.login_to_MC_for_status()
			self.status.write("CLI\n")
			self.status.write("show -d properties=FirmwareVersion " + Target + "\n")
			self.status.write("exit\n")
			Response_buf = self.status.read_until('Exit the Session',120)
			fw_version = self.parse_response_property(Response_buf,'FirmwareVersion = ')
			self.status.write("exit\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_MC_FW_Version failed')
		return fw_version
#################################################################################################################
	def get_Rack_Info(self):
		NumberOfBC = 0
		iRet='PASS'
		global Powerbay_Number_map,BC_IpAddress_map
		try:
			Powerbay_Number_map = []
			BC_IpAddress_map = []

			print self.logging("\n*****************************************")
			print self.logging("MC IpAddress           = %s"%(self.HOST_IP))

			MC_FW_Version = self.get_FW_Version("/MCManager")
			print self.logging("MC Firmware Version    = %s"%(MC_FW_Version))

			isRackPowerON = self.get_Rack_PowerState()
			print self.logging("Rack Power State       = %s"%(isRackPowerON))
			
			self.login_to_MC()
			self.get_Powerbay_number()
			Total_Powerbay = Powerbay_Number_map.__len__()
			print self.logging("Total PowerBay Present = %s"%(Total_Powerbay))
			
			self.login_to_MC()
			if isRackPowerON == 'ON':
				self.get_BC_IpAddress()
				NumberOfBC = BC_IpAddress_map.__len__()
			else:
				self.login_to_MC_for_status()
				self.status.write("CLI\n")
				self.status.write("start -f Rack1\n")
				print self.logging('Rack PowerState is OFF. please wait 480 seconds for rack start')
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(480);
				self.status.write("exit\n")
				self.status.write("exit\n")
				self.get_BC_IpAddress()
				NumberOfBC = BC_IpAddress_map.__len__()
			
			print self.logging("Total Blocks Presence  = %s"%(NumberOfBC))
			print self.logging("Total Loop count       = %s"%(self.loop ))
			print self.logging("Debug Mode             = %s"%(self.debug_mode ))
			print self.logging("*****************************************\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_Info failed')
		return iRet
#################################################################################################################
	def IdLedState_ON_OFF(self, MC_IP, loop_count = '', UserName = '', Password = ''):
		global BC_IpAddress_map, Powerbay_Number_map, NumberOfBC, Number_of_Powerbay
		
		try:			
			iRet = 'PASS'
			iRet_Final ='PASS'
			iRet_ON_case_star = 'PASS'
			iRet_OFF_case_star = 'PASS'
			
			if MC_IP != '':
				self.HOST_IP = MC_IP

			if UserName != '':
				self.user = str(UserName)

			if Password != '':
				self.password = str(Password)

			self.create_log_folder(self.log_file)
			debug = self.debug_mode.lower()
			if debug == "no":
				self.blockPrint()

			if loop_count != '':
				self.loop = loop_count

			self.check_ping()

			print self.logging("\n*******************************************************************************")
			print self.logging("*                    IdLed ON-OFF Test start on %s                 *"%(self.HOST_IP))
			print self.logging("*******************************************************************************\n")
			
			self.get_Rack_Info()
			NumberOfBC = BC_IpAddress_map.__len__()
			Number_of_Powerbay = Powerbay_Number_map.__len__()
			self.login_to_MC()
			start_count = 1
			while (start_count <= int(self.loop)):
				iRet = 'PASS'
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n*******************************************************************************")
				print self.logging("*                             Test Cycle Number = %s                           *"%(start_count))
				print self.logging("*******************************************************************************\n")

				print self.logging("---------------------------------------------------------")
				print self.logging("|                     IdLed ON Test                     |")
				print self.logging("---------------------------------------------------------")
				iRet_OFF_case = self.Execution_start('ON')
			
				print self.logging("\n---------------------------------------------------------")
				print self.logging("|                     IdLed OFF Test                    |")
				print self.logging("---------------------------------------------------------")
				iRet_ON_case  = self.Execution_start('OFF')

				print self.logging("\n---------------------------------------------------------")
				print self.logging("|                     IdLed ON Test for star support    |")
				print self.logging("---------------------------------------------------------")
				iRet_ON_case_star = self.Execution_start_star('ON')

				print self.logging("\n---------------------------------------------------------")
				print self.logging("|                     IdLed OFF Test for star support   |")
				print self.logging("---------------------------------------------------------")
				iRet_OFF_case_star = self.Execution_start_star('OFF')
				
				if iRet_OFF_case == 'FAIL':
					iRet = 'FAIL'
					iRet_Final = 'FAIL'

				if iRet_ON_case == 'FAIL':
					iRet = 'FAIL'
					iRet_Final = 'FAIL'
					
				if iRet_OFF_case_star == 'FAIL':
					iRet = 'FAIL'
					iRet_Final = 'FAIL'
					
				if iRet_ON_case_star == 'FAIL':
					iRet = 'FAIL'
					iRet_Final = 'FAIL'

				print self.logging("\n*******************************************************************************")
				print self.logging("*                          IdLed ON-OFF Test : %s                           *"%(iRet))
				print self.logging("*******************************************************************************\n")
				start_count = start_count + 1
			print self.logging("*                             Overall result : %s                           *"%(iRet_Final))
			return iRet_Final
		except:
			print self.logging("Interrupt signal or script stopped by user")
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			return 'FAIL'
#################################################################################################################

if __name__ == "__main__":
	obj=IdLed_test()
	obj.main(sys.argv[1:])
