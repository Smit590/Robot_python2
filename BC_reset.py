import os, sys, time, shutil, re
import socket, datetime, telnetlib, getopt
import traceback
#from robot.libraries.BuiltIn import BuiltIn

BC_IpAddress_map = []
Powerbay_Number_map = []
Sled_Bit_map = []
NumberOfBC = ''

Sled_reset_log, current_dir, subdir = ['','','']
#################################################################################################################
####################################Steps followed for this test script##########################################
#################################################################################################################
#1. login to MC and disable grouping property of the rack.
#2. Execute "Sled Soft Reset " if test fails/pass continue test for number of iterations.
#3. Execute "Sled Hard Reset " if test fails/pass continue test for number of iterations.
#################################################################################################################

class BC_reset:
	def __init__(self):
		self.tn = None
		self.status  = None
		self.user = 'root'
		self.password = 'calvin'
		#~ self.log_file = 'Sled_reset_test.log'
		timestr = time.strftime("%Y%m%d-%H%M%S")
		file_name = "BC_reset_test_" + timestr + ".log"
		self.log_file = file_name
		self.loop = '1'
		self.debug_mode = 'yes'
		self.HOST_IP = ''
		self.Failed_loop_num_buf = ''
#################################################################################################################
	def usage(self):
		print "usage : python Sled_reset.py"
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
				#print " MC in not present "
				#sys.exit()

			self.BC_reset('','','','')
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
		global Sled_reset_log,current_dir,subdir
		try:
			filepath = os.path.join(current_dir, subdir, str(self.HOST_IP), Sled_reset_log)
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
		global Sled_reset_log,current_dir,subdir
		try:
			current_dir = os.path.dirname(os.path.realpath(__file__))
			subdir = "../logs"

			if not os.path.exists(current_dir+"/"+subdir):
				os.mkdir(os.path.join(current_dir, subdir))

			if not os.path.exists(current_dir+"/"+subdir+"/"+str(self.HOST_IP)):
				os.mkdir(os.path.join(current_dir, subdir,str(self.HOST_IP)))

			Sled_reset_log = log_files
			New_Sled_reset_log = current_dir + "/" + subdir + "/" + str(self.HOST_IP) + "/" + Sled_reset_log
			old_Sled_reset_log = New_Sled_reset_log+"_old"

			if os.path.exists(old_Sled_reset_log):
				os.remove(old_Sled_reset_log)

			if os.path.exists(New_Sled_reset_log):
				os.rename(New_Sled_reset_log,old_Sled_reset_log)

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('create_log_folder failed')
		else:
			print self.logging("\ncreate %s successfully"%(New_Sled_reset_log))
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
#################################################################################################################
	def check_Test_Result(self,buf,expected_state):
		status = 'FAIL'
		PASS = 0
		FAIL = 0
		try:
			for line in buf.splitlines():
				if 'PowerState = ' in line:
					value = line.split()[-1]
					if (value == expected_state or value == "NA"):
						PASS += 1
					else:
						FAIL += 1
				elif 'PresenceState = ' in line:
					if (expected_state == 'OFF'):
						value = line.split()[-1]
						if (value == 'PRESENT'):
							FAIL += 1
				elif expected_state == 'ON':
					if 'Invalid target address!' in line:
						FAIL += 1

			if FAIL is 0:
				status = 'PASS'
			return status
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('check_result failed')

#################################################################################################################
	def get_MC_FW_Version(self):
		fw_version = 'NA'
		try:
			self.status.write("CLI\n")
			self.status.write("show -d properties=FirmwareVersion /MCManager\n")
			self.status.write("exit\n")
			Response_buf = self.status.read_until('Exit the Session',120)
			fw_version = self.parse_response_property(Response_buf,'FirmwareVersion = ')
			return fw_version
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_LastPowerChangeStatus failed')
#################################################################################################################
	def get_SystemUptime(self,Target):
		value = 'NA'
		try:
			self.status.write('CLI\n')
			self.status.write('show -d properties=SystemUptime '+ Target + '\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'SystemUptime = ' in line:
					value = line.split()[-1]
			return value
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_PowerState failed')
#################################################################################################################
	def get_PresenceState(self,Target):
		value = 'NA'
		try:
			self.status.write('CLI\n')
			self.status.write('show -d properties=PresenceState '+ Target + '\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'PresenceState = ' in line:
					value = line.split()[-1]
			return value
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_PowerState failed')
#################################################################################################################
	def get_PowerState(self,Target):
		value = 'NA'
		try:
			self.status.write('CLI\n')
			self.status.write('show -d properties=PowerState '+ Target + '\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'PowerState = ' in line:
					value = line.split()[-1]
			return value
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_PowerState failed')
#################################################################################################################

	def get_Rack_LastPowerChangeStatus(self):
		start_stop_status = 'NA'
		try:
			self.status.write("CLI\n")
			time.sleep(1)
			self.status.write("show -d properties=LastPowerChangeStatus RACK1\n")
			time.sleep(1)
			self.status.write("exit\n")
			time.sleep(1)
			Response_buf = self.status.read_until('Exit the Session',120)
			start_stop_status = self.parse_response_property(Response_buf,'LastPowerChangeStatus = ')
			return start_stop_status
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_LastPowerChangeStatus failed')

#################################################################################################################
	def get_Powerbay_number(self):
		global Powerbay_Number_map
		PSU_Present='0'
		try:
			self.status.write("CLI\n")
			self.status.write('show -d properties=NumberOfPSU,PowerBayNumber Rack1/PowerBay*\n')
			self.status.write("exit\n")
			buf=self.status.read_until('Exit the Session')
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
#################################################################################################################
	def get_BC_IpAddress(self):
		try:
			self.status.write('CLI\n')
			self.status.write('show -d properties=IpAddress Rack1/block*/BC\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
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
#################################################################################################################
	def get_BC_PresenceState(self,Target):
		value = 'ABSENT'
		try:
			self.status.write('CLI\n')
			self.status.write('show -d properties=PresenceState '+ Target + '\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'PresenceState = ' in line:
					value = line.split()[-1]
			return value
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_BC_PresenceState failed')
#################################################################################################################
	def get_sled_presence(self,Block_No):
		sled_presence = 'NA'
		try:
			self.status.write("CLI\n")
			time.sleep(1)
			self.status.write("show -d properties=SledNumbers Rack1/Block" + Block_No + "/BC\n")
			time.sleep(1)
			self.status.write("exit\n")
			time.sleep(1)
			Response_buf = self.status.read_until('Exit the Session',120)
			sled_presence = self.parse_response_property(Response_buf,'SledNumbers = ')
			return sled_presence
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_LastPowerChangeStatus failed')

#################################################################################################################
	def get_Total_Sleds(self):
		Count = 0
		try:
			self.status.write("CLI\n")
			self.status.write('show -d properties=PresenceState Rack1/Block*/Sled*\n')
			self.status.write("exit\n")
			self.status.write("exit\n")
			buf=self.status.read_all()

			for line in buf.splitlines():
				if 'PresenceState = ' in line:
					value = line.split()[-1]
					if (value == 'PRESENT'):
						value = line.split()[-1]
						Count += 1
			return Count
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Total_Sleds failed')
#################################################################################################################
	def get_sled_bitmap_per_block(self,block_num):
		global Sled_Bit_map
		try:
			self.status.write("CLI\n")
			self.status.write('show -d properties=SledNumbers Rack1/Block'+block_num+'/BC\n')
			self.status.write("exit\n")
			time.sleep(1)
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'SledNumbers = ' in line:
					value = line.split()[-1]
					if (value != "NA"):
						Sled_Bit_map.append(value)
					else:
						Sled_Bit_map.append("NA")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_sled_bitmap_per_block failed')
#################################################################################################################
	def parse_response_property(self, tn_buf, property_name):
		operation_status = 'NA'
		try:
			tn_buf_ = str(tn_buf)
			for line in tn_buf_.splitlines():
				if str(property_name) in line:
					line = line.strip()
					if (line.split()[-1]) != '=':
						value = line.split("= ")[1]
						operation_status = value
					else:
						print self.logging("skip line: %s " % (line))
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('parse_response_property failed')

		return operation_status
#################################################################################################################
	def get_Rack_Info(self):
		try:
			global BC_IpAddress_map, NumberOfBC
			self.login_to_MC_for_status()

			print self.logging("\n*****************************************")
			print self.logging("MC IpAddress           = %s"%(self.HOST_IP))

			MC_FW_Version = self.get_MC_FW_Version()
			print self.logging("MC Firmware Version    = %s"%(MC_FW_Version))

			isRackPowerON = self.get_PowerState("Rack1")
			print self.logging("Rack PowerState        = %s"%(isRackPowerON))

			self.get_Powerbay_number()
			Total_PowerBay = Powerbay_Number_map.__len__()
			print self.logging("Total PowerBay Present = %s"%(Total_PowerBay))

			if isRackPowerON == 'ON':
				self.get_BC_IpAddress()
				NumberOfBC = BC_IpAddress_map.__len__()
			else:
				self.status.write("CLI\n")
				self.status.write("start -f Rack1\n")
				print self.logging('Rack PowerState is OFF. please wait 480 seconds for rack start')
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(480);
				self.status.write("exit\n")
				self.get_BC_IpAddress()
				NumberOfBC = BC_IpAddress_map.__len__()

			print self.logging("Total Blocks Presence  = %s"%(NumberOfBC))

			size = BC_IpAddress_map.__len__()
			for index in range(size):
				self.get_sled_bitmap_per_block(str(BC_IpAddress_map[index]))

			totalSleds = self.get_Total_Sleds()
			print self.logging("Total Sleds Presence   = %s"%(totalSleds))

			print self.logging("Test loop count        = %s"%(self.loop ))
			print self.logging("Debug Mode             = %s"%(self.debug_mode ))
			print self.logging("*****************************************")
			self.status = None
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_Info failed')
#################################################################################################################
	def getAllProperty(self,expected_state):
		iRet = 'PASS'
		try:
			self.login_to_MC_for_status()
			time.sleep(5)
			size = BC_IpAddress_map.__len__()
			if size != 0:
				time.sleep(5)
				for index in range(size):
					BC_Presence = self.get_PresenceState('Rack1/Block'+str(BC_IpAddress_map[index])+'/BC')
					print self.logging("Rack1/Block%s/BC: PresenceState    = %s"%(BC_IpAddress_map[index],BC_Presence))
					BC_SystemUptime = self.get_SystemUptime('Rack1/Block'+str(BC_IpAddress_map[index])+'/BC')
					print self.logging("Rack1/Block%s/BC: SystemUptime     = %s"%(BC_IpAddress_map[index],BC_SystemUptime))
					if expected_state == 'PRESENT':
						if BC_Presence != 'PRESENT':
							iRet = 'FAIL'
					time.sleep(1)
				IM_SystemUptime = self.get_SystemUptime('Rack1/Powerbay1/IM')
				print self.logging("Rack1/Powerbay1/IM: SystemUptime  = %s"%(IM_SystemUptime))

			self.status.write('exit\n')
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('getAllProperty failed')
#################################################################################################################
	def soft_reset_command(self, cmd):
		status = 'FAIL'
		try:
			self.tn.write("CLI\n")
			time.sleep(5)
			self.tn.write( cmd + '\n')
			time.sleep(5)
			buf=self.tn.read_until('Do you want to reset? [y/n]',10)
			if 'Do you want to reset? [y/n]' in buf:
				self.tn.write( 'y\n')
				buf=self.tn.read_until('Command request is in progress. This will take few seconds to complete!',10)
				if 'Command request is in progress. This will take few seconds to complete!' in buf:
					status = 'PASS'
				elif 'This will take a few minutes to complete.' in buf:
					status ='PASS'

			self.tn.write("exit\n")
			return status
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('execute_command failed')
#################################################################################################################
	def hard_reset_command(self, cmd):
		status = 'FAIL'
		try:
			self.tn.write("CLI\n")
			time.sleep(5)
			self.tn.write( cmd + '\n')
			time.sleep(5)
			buf=self.tn.read_until('Command request is in progress. This will take few seconds to complete!',10)
			if 'Command request is in progress. This will take few seconds to complete!' in buf:
				status = 'PASS'
			elif 'This will take a few minutes to complete.' in buf:
				status ='PASS'
				
			self.tn.write("exit\n")
			return status
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('execute_command failed')
#################################################################################################################
	def Execution_start_llcDebug(self, command, force_opt):
		global NumberOfBC
		iRet = 'FAIL'
		try:
			self.login_to_MC()
			time.sleep(2)
			size = BC_IpAddress_map.__len__()
			if size != 0:
				time.sleep(2)
				for index in range(size):
					if force_opt != '-f':
						self.tn.write( command + BC_IpAddress_map[index] +" 10.253.0."+BC_IpAddress_map[index]+'\n')
						buf=self.tn.read_until('BC is Rebooting Now.....',10)
						print self.logging("\nbuf =  %s"%(buf))
						if 'BC is Rebooting Now.....' in buf: 
							iRet='PASS'
						print self.logging("Execute \"llcDebug resetLLC,BC%s 10.253.0.%s\" : %s"%(BC_IpAddress_map[index],BC_IpAddress_map[index],iRet))
					else:
						self.tn.write( command + BC_IpAddress_map[index] +" 10.253.0.17\n")
						buf=self.tn.read_until('BC is Rebooting Now.....',10)
						print self.logging("\nbuf =  %s"%(buf))
						if 'BC is Rebooting Now.....' in buf: 
							iRet='PASS'
						print self.logging("Execute \"llcDebug resetLLC,BC%s 10.253.0.17\" : %s"%(BC_IpAddress_map[index],iRet))
					time.sleep(2)
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('Execution_start failed')
#################################################################################################################
	def Execution_start_star(self, command, force_opt):
		global NumberOfBC
		iRet = 'FAIL'
		try:
			self.login_to_MC()
			time.sleep(5)
			if force_opt == '-f':
				iRet = self.hard_reset_command(str(command + ' -f Rack1/Block*/BC'))
				print self.logging("Execute \"Reset -f Rack1/Block*/BC\" : %s"%(iRet))
			else:
				iRet = self.soft_reset_command(str(command + ' Rack1/Block*/BC'))
				print self.logging("Execute \"Reset Rack1/Block*/BC\" : %s "%(iRet)) 
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('Execution_start failed')

#################################################################################################################
	def Execution_start(self, command, force_opt):
		global NumberOfBC
		iRet = 'FAIL'
		try:
			self.login_to_MC()
			time.sleep(2)
			size = BC_IpAddress_map.__len__()
			if size != 0:
				time.sleep(5)
				for index in range(size):
					if force_opt == '-f':
						iRet = self.hard_reset_command(str(command + ' -f Rack1/Block'+str(BC_IpAddress_map[index])+'/BC'))
						print self.logging("\nExecute \"Reset -f Rack1/Block%s/BC\" : %s"%(BC_IpAddress_map[index],iRet))
					else:
						iRet = self.soft_reset_command(str(command + ' Rack1/Block'+str(BC_IpAddress_map[index])+'/BC'))
						print self.logging("\nExecute \"Reset Rack1/Block%s/BC\" : %s "%(BC_IpAddress_map[index],iRet)) 
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('Execution_start failed')

#################################################################################################################
	def BC_Hard_reset(self):
		iRet = 'PASS'
		start_count = 1
		print self.logging("\n\n*******************************************************************************")
		print self.logging("*                BC Hard Reset Test start on %s                  *"%(self.HOST_IP))
		print self.logging("*******************************************************************************\n")
		try:
			while (start_count <= int(self.loop)):
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("\n-------------------------------------------------------------------")
				print self.logging("|                     BC Hard Reset operation                   |")
				print self.logging("-------------------------------------------------------------------")

				self.Execution_start('Reset','-f')
			
				print self.logging("\n---------------------------")
				print self.logging("|       Wait 240 sec      |")
				print self.logging("---------------------------\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(240)
			
				iRet = self.getAllProperty('PRESENT')
				if iRet == 'FAIL':
					self.Failed_loop_num_buf = self.Failed_loop_num_buf + "BC Hard Reset failed  : Test Cycle Number : " + str(start_count) + "\n"
					print self.logging("\n************************************************************")
					print self.logging("*                  BC Hard Reset test result                  *")
					print self.logging("************************************************************")
					print self.logging(self.Failed_loop_num_buf)
					
				print self.logging("\n*************************************")
				print self.logging("*    BC Hard Reset test : %s    *"%(iRet))
				print self.logging("*************************************")
				start_count = start_count + 1
			return iRet

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('BC_Hard_reset failed')
#################################################################################################################
	def BC_hard_reset_llcDebug(self):
		start_count = 1
		iRet = 'PASS'
		print self.logging("\n\n****************************************************************************************")
		print self.logging("*                BC Hard Reset Test throgh llcDebug command start on %s                  *"%(self.HOST_IP))
		print self.logging("********************************************************************************************\n")
		try:
			while (start_count <= int(self.loop)):
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("\n-------------------------------------------------------------------")
				print self.logging("|                     BC Hard Reset operation                   |")
				print self.logging("-------------------------------------------------------------------")

				self.Execution_start_llcDebug('llcDebug resetLLC,BC','-f')
				print self.logging("\n---------------------------")
				print self.logging("|       Wait 240 sec      |")
				print self.logging("---------------------------\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(240)
			
				iRet = self.getAllProperty('PRESENT')

				print self.logging("\n*************************************")
				print self.logging("*     BC hard Reset test through llcDebug command : %s   *"%(iRet))
				print self.logging("*************************************")
				start_count = start_count + 1
			
			if iRet == 'FAIL':
				self.Failed_loop_num_buf = self.Failed_loop_num_buf + "Sled Soft Reset failed  : Test Cycle Number : " + str(start_count) + "\n"
				print self.logging("\n************************************************************")
				print self.logging("*                  BC hard Reset test result through llcDebug command            *")
				print self.logging("************************************************************")
				print self.logging(self.Failed_loop_num_buf)
			return iRet

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('BC_soft_reset failed')
#################################################################################################################
	def BC_soft_reset_llcDebug(self):
		start_count = 1
		iRet = 'PASS'
		print self.logging("\n\n***************************************************************************************")
		print self.logging("*                BC Soft Reset Test throgh llcDebug command start on %s                  *"%(self.HOST_IP))
		print self.logging("********************************************************************************************\n")
		try:
			while (start_count <= int(self.loop)):
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("\n-------------------------------------------------------------------")
				print self.logging("|                     BC Soft Reset operation                   |")
				print self.logging("-------------------------------------------------------------------")

				self.Execution_start_llcDebug('llcDebug resetLLC,BC','')
				print self.logging("\n---------------------------")
				print self.logging("|       Wait 240 sec      |")
				print self.logging("---------------------------\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(240)
			
				iRet = self.getAllProperty('PRESENT')

				print self.logging("\n*************************************")
				print self.logging("*     BC Soft Reset test through llcDebug command : %s   *"%(iRet))
				print self.logging("*************************************")
				start_count = start_count + 1
			
			if iRet == 'FAIL':
				self.Failed_loop_num_buf = self.Failed_loop_num_buf + "Sled Soft Reset failed  : Test Cycle Number : " + str(start_count) + "\n"
				print self.logging("\n************************************************************")
				print self.logging("*                  BC Soft Reset test result through llcDebug command            *")
				print self.logging("************************************************************")
				print self.logging(self.Failed_loop_num_buf)
			return iRet

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('BC_soft_reset failed')
#################################################################################################################
	def BC_hard_reset_star(self):
		start_count = 1
		iRet = 'PASS'
		print self.logging("\n\n*******************************************************************************")
		print self.logging("*                BC hard Reset star Test start on %s                  *"%(self.HOST_IP))
		print self.logging("*******************************************************************************\n")
		try:
			while (start_count <= int(self.loop)):
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("\n-------------------------------------------------------------------")
				print self.logging("|                     BC hard Reset star operation                   |")
				print self.logging("-------------------------------------------------------------------")

				self.Execution_start_star('Reset','-f')
				print self.logging("\n---------------------------")
				print self.logging("|       Wait 240 sec      |")
				print self.logging("---------------------------\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(240)
			
				iRet = self.getAllProperty('PRESENT')

				print self.logging("\n*************************************")
				print self.logging("*     BC hard Reset star test : %s   *"%(iRet))
				print self.logging("*************************************")
				start_count = start_count + 1
			
			if iRet == 'FAIL':
				self.Failed_loop_num_buf = self.Failed_loop_num_buf + "BC Soft Reset star failed  : Test Cycle Number : " + str(start_count) + "\n"
				print self.logging("\n************************************************************")
				print self.logging("*                  BC Soft Reset star test result             *")
				print self.logging("************************************************************")
				print self.logging(self.Failed_loop_num_buf)
			return iRet

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('BC_soft_reset failed')
#################################################################################################################
	def BC_soft_reset_star(self):
		start_count = 1
		iRet = 'PASS'
		print self.logging("\n\n*******************************************************************************")
		print self.logging("*                BC Soft Reset star Test start on %s                  *"%(self.HOST_IP))
		print self.logging("*******************************************************************************\n")
		try:
			while (start_count <= int(self.loop)):
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("\n-------------------------------------------------------------------")
				print self.logging("|                     BC Soft Reset star operation                   |")
				print self.logging("-------------------------------------------------------------------")

				self.Execution_start_star('Reset','')
				print self.logging("\n---------------------------")
				print self.logging("|       Wait 240 sec      |")
				print self.logging("---------------------------\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(240)
			
				iRet = self.getAllProperty('PRESENT')

				print self.logging("\n*************************************")
				print self.logging("*     BC Soft Reset star test : %s   *"%(iRet))
				print self.logging("*************************************")
				start_count = start_count + 1
			
			if iRet == 'FAIL':
				self.Failed_loop_num_buf = self.Failed_loop_num_buf + "BC Soft Reset star failed  : Test Cycle Number : " + str(start_count) + "\n"
				print self.logging("\n************************************************************")
				print self.logging("*                  BC Soft Reset star test result             *")
				print self.logging("************************************************************")
				print self.logging(self.Failed_loop_num_buf)
			return iRet

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('BC_soft_reset failed')
#################################################################################################################
	def BC_soft_reset(self):
		start_count = 1
		iRet = 'PASS'
		print self.logging("\n\n*******************************************************************************")
		print self.logging("*                BC Soft Reset Test start on %s                  *"%(self.HOST_IP))
		print self.logging("*******************************************************************************\n")
		try:
			while (start_count <= int(self.loop)):
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("\n-------------------------------------------------------------------")
				print self.logging("|                     BC Soft Reset operation                   |")
				print self.logging("-------------------------------------------------------------------")

				self.Execution_start('Reset','')
				print self.logging("\n---------------------------")
				print self.logging("|       Wait 240 sec      |")
				print self.logging("---------------------------\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(240)
				iRet = self.getAllProperty('PRESENT')

				print self.logging("\n*************************************")
				print self.logging("*     BC Soft Reset test : %s   *"%(iRet))
				print self.logging("*************************************")
				start_count = start_count + 1
			
			if iRet == 'FAIL':
				self.Failed_loop_num_buf = self.Failed_loop_num_buf + "Sled Soft Reset failed  : Test Cycle Number : " + str(start_count) + "\n"
				print self.logging("\n************************************************************")
				print self.logging("*                  BC Soft Reset test result             *")
				print self.logging("************************************************************")
				print self.logging(self.Failed_loop_num_buf)
			return iRet

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('BC_soft_reset failed')
#################################################################################################################
	def BC_reset(self, MC_IP, loop_count = '', UserName = '', Password = ''):
		try:
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

			count = 1
			iRet = 'PASS'
			status= 'FAIL'
			if loop_count != '':
				self.loop = loop_count

			self.check_ping()
			self.get_Rack_Info()
			self.login_to_MC()
			
			#~ iRet_soft = self.BC_soft_reset()  // line by line
			#~ iRet_hard = self.BC_Hard_reset()  // line by line 
			#~ iRet_llcDebug_soft = self.BC_soft_reset_llcDebug() // llcDebug line by line
			#~ iRet_llcDebug_hard = self.BC_hard_reset_llcDebug()   // 
			iRet_soft_star = self.BC_soft_reset_star() 
			iRet_hard_star = self.BC_hard_reset_star()
			
			if iRet_soft_star == 'FAIL' or iRet_hard_star == 'FAIL' :
				iRet = 'FAIL'
			print self.logging("\n*******************************************************************************")
			print self.logging("*                   BC Soft/Hard Reset Test result : %s                   *"%(iRet))
			print self.logging("*******************************************************************************\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			return 'FAIL'	
			#~ raise RuntimeError('BC_reset failed')
		return iRet
#################################################################################################################
if __name__ == "__main__":
    obj=BC_reset()
    obj.main(sys.argv[1:])
