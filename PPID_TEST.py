import os, sys, time, shutil, re
import socket, datetime, telnetlib, getopt
import traceback
#from robot.libraries.BuiltIn import BuiltIn

BC_IpAddress_map = []
Powerbay_Number_map = []
Sled_Bit_map = []
NumberOfBC = ''

PPID_log, current_dir, subdir = ['','','']

#################################################################################################################
####################################Steps followed for this test script##########################################
#################################################################################################################
#1.  login to MC and get info of rack.
#2.  if login and acquired info is correct start test cycle.
#3.  get PPID value for revert back purpose.
#4.  set PPID value(static) through command and reboot MC.
#5.  After MC up check PPID value and compare it with static value which set earlier.
#6.  Repeat step no.4 but value should be more than 64 bytes and check the response.
#7.  set PPID value(static) through manufacturing.conf file and reboot MC.
#8.  After MC up check PPID value on CLI, flash/data0/PPID.bin and opt/dell/mc/conf/infoarea.bin and value should be there as we set by step number 7.
#9.  set PPID value(static) through manufacturing.conf file more than 64 bytes and reboot MC.
#10. After MC up check PPID value on CLI, flash/data0/PPID.bin and opt/dell/mc/conf/infoarea.bin and value should be set upto 64 bytes only.
#11. Perform all test cycles and repeating above steps. 
#12. set revert back PPID value which we get from step 3 and reboot MC.
#13. Check PPID value on CLI and it should be same as we get value from step 3 and display result of test case. 
#################################################################################################################

class PPID_TEST:
	def __init__(self):
		self.tn = None
		self.status  = None
		self.user = 'root'
		self.password = 'calvin'
		timestr = time.strftime("%Y%m%d-%H%M%S")
		file_name = "PPID_test_" + timestr + ".log"
		self.log_file = file_name
		self.loop = '1'
		self.debug_mode = 'yes'
		self.HOST_IP = ''
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

			self.SET_PPID_TEST('','','','')
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
		global PPID_log,current_dir,subdir
		try:
			filepath = os.path.join(current_dir, subdir, str(self.HOST_IP), PPID_log)
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
		global PPID_log,current_dir,subdir
		try:
			current_dir = os.path.dirname(os.path.realpath(__file__))
			subdir = "../logs"

			if not os.path.exists(current_dir+"/"+subdir):
				os.mkdir(os.path.join(current_dir, subdir))

			if not os.path.exists(current_dir+"/"+subdir+"/"+str(self.HOST_IP)):
				os.mkdir(os.path.join(current_dir, subdir,str(self.HOST_IP)))

			PPID_log = log_files
			New_PPID_log = current_dir + "/" + subdir + "/" + str(self.HOST_IP) + "/" + PPID_log
			old_PPID_log = New_PPID_log+"_old"

			if os.path.exists(old_PPID_log):
				os.remove(old_PPID_log)

			if os.path.exists(New_PPID_log):
				os.rename(New_PPID_log,old_PPID_log)

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('create_log_folder failed')
		else:
			print self.logging("\ncreate %s successfully"%(New_PPID_log))
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
			raise RuntimeError('login_to_MC_for_status failed')
			return 'FAIL'
#############################################################################################################
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
			return 'FAIL'
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
			return 'FAIL'
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
					value = line.split("= ")[1]
					if 'NA' in value:
						continue
					PSU_Present='1'											# assign to actual PB only

				if "PowerBayNumber = " in line:
					powerbayno=line.split("= ")[1]
					if PSU_Present =='1':
						powerbayno = powerbayno.replace(' ', '')
						Powerbay_Number_map.append(powerbayno)
					PSU_Present='0'
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Powerbay_number failed')
			return 'FAIL'
#################################################################################################################
	def get_BC_IpAddress(self):
		try:
			self.status.write('CLI\n')
			self.status.write('show -d properties=IpAddress Rack1/block*/BC\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'IpAddress = ' in line:
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
			return 'FAIL'
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
			return 'FAIL'
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
			return 'FAIL'
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
			return 'FAIL'
#################################################################################################################
	def get_PPID(self):
		try:
			self.login_to_MC_for_status()
			self.status.write("CLI\n")
			self.status.write('show -d properties=PPID /MCManager\n')
			self.status.write("exit\n")
			time.sleep(1)
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'PPID = ' in line:
					value = line.split()[-1]
					print self.logging("OLD PPID_value = %s"%(value))
			return value
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_PPID failed')
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
						value = line.split("= ")[1]
						operation_status = value
					else:
						print self.logging("skip line: %s " % (line))
			return operation_status
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('parse_response_property failed')
			return 'FAIL'
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
			return 'FAIL'
#################################################################################################################
	def PPID_SET_FROM_CONF_MORE_THAN_64(self):
		iRet = 'PASS'
		msg ='MC1_ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz_12345?78910'
		PPID_STRING_EXPECTED = 'MC1_ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz_12345?'
		try:
			print self.logging("\n-------------------------------------------------------------------")
			print self.logging("|        Set PPID operation start for > 64 bytes from conf          |")
			print self.logging("-------------------------------------------------------------------")
			print self.logging("Going to set PPID from conf = %s "%(msg))
			self.login_to_MC()
			cmd = "sed -i /PPID=/s/.*./PPID=\'\MC1_ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz_12345?78910\'""/ /opt/dell/mc/conf/manufacturing.conf\n"
			PPID_CLI = self.Command_Response_Value(cmd)
			print self.logging("\nPPID found on CLI is = %s"%(PPID_CLI))
			self.tn.write("CLI\n")
			self.tn.write("ls /mcmanager\n")
			self.tn.write("exit\n")
			buf=self.tn.read_until('Exit the Session',10)
			SerialNumber = self.parse_response_property(buf,'SerialNumber = ')
			if PPID_CLI == PPID_STRING_EXPECTED:
				print self.logging("\nPPID set successfully on CLI.")
			else:
				print self.logging("Failed to set PPID.")
				iRet = 'FAIL'

			self.tn.write('cat flash/data0/PPID.bin\n')
			buf=self.tn.read_until(PPID_STRING_EXPECTED,3)
			MC1_FIRST_PPID_BIN = buf.find("MC1")
			PPID_BIN = buf[MC1_FIRST_PPID_BIN:]
			
			if PPID_STRING_EXPECTED == PPID_BIN:
				print self.logging("\nPPID found in flash/data0/PPID.bin is = %s"%(PPID_STRING_EXPECTED))
				print self.logging("\nPPID is set successfully in flash/data0/PPID.bin.")
			else:
				print self.logging("\nPPID is fail to set in flash/data0/PPID.bin.")
				iRet = 'FAIL'
			
			self.tn.write('cat opt/dell/mc/conf/infoarea.bin\n')
			buf1=self.tn.read_until(SerialNumber,5)
			MC1_FIRST = buf1.find("MC1")
			MC1_SECOND = buf1.rfind("?")
			PPID_INFOAREA = buf1[MC1_FIRST:MC1_SECOND+1]
			print self.logging("\nPPID_INFOAREA= %s"%(PPID_INFOAREA))
			if PPID_INFOAREA == PPID_STRING_EXPECTED:
				print self.logging("\nPPID found in opt/dell/mc/conf/infoarea.bin is = %s"%(PPID_STRING_EXPECTED))
				print self.logging("\nPPID is set successfully in opt/dell/mc/conf/infoarea.bin.")
			else:
				print self.logging("\nPPID is fail to set in opt/dell/mc/conf/infoarea.bin.")
				iRet = 'FAIL'
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('PPID_SET_FROM_CONF_MORE_THAN_64 failed')
			return 'FAIL'
#################################################################################################################
	def PPID_SET_MORE_THAN_64(self, string_ppid):
		iRet = 'FAIL'
		msg = 'Incorrect Arguments'
		try:
			print self.logging("\n-------------------------------------------------------------------")
			print self.logging("|            Set PPID operation start for > 64 bytes               |")
			print self.logging("-------------------------------------------------------------------")
			self.login_to_MC()
			time.sleep(3)
			self.tn.write('set_ppid '+string_ppid+'\n')
			buf=self.tn.read_until('Incorrect Arguments',10)
			
			if msg in buf:
				print self.logging(" Response is Incorrect Arguments")
				print self.logging(" PPID can't be set for more than 64 bytes data.")
				print self.logging(" Result : Success ")
				iRet = 'PASS'
			else:
				print self.logging("\nPPID get failure to prevent data to set more than 64 bytes.")
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('start failed')
			return 'FAIL'
#################################################################################################################
	def PPID_SET_FROM_CONF(self):
		iRet = 'PASS'
		PPID_STRING = 'MC1_12345678910'
		try:
			print self.logging("\n-------------------------------------------------------------------")
			print self.logging("|             Set PPID operation start from conf file               |")
			print self.logging("-------------------------------------------------------------------")
			print self.logging("Going to set PPID from conf = %s "%(PPID_STRING))
			self.login_to_MC()
			time.sleep(3)
			cmd = "sed -i /PPID=/s/.*./PPID=\'\MC1_12345678910\'""/ /opt/dell/mc/conf/manufacturing.conf\n"
			PPID = self.Command_Response_Value(cmd)
			print self.logging("\nPPID found on CLI is = %s"%(PPID))
			self.tn.write('cat flash/data0/PPID.bin\n')
			buf=self.tn.read_until(PPID_STRING,3)
			
			if PPID == PPID_STRING:
				print self.logging("\nPPID set successfully on CLI.")
			else:
				print self.logging("Failed to set PPID.")
				iRet = 'FAIL'

			if PPID_STRING in buf:
				print self.logging("\nPPID found in flash/data0/PPID.bin is = %s"%(PPID_STRING))
				print self.logging("\nPPID is set successfully in flash/data0/PPID.bin.")
			else:
				print self.logging("\nPPID is fail to set in flash/data0/PPID.bin.")
				iRet = 'FAIL'
			
			self.tn.write('cat opt/dell/mc/conf/infoarea.bin\n')
			buf1=self.tn.read_until(PPID_STRING,3)
			
			if PPID_STRING in buf1:
				print self.logging("\nPPID found in opt/dell/mc/conf/infoarea.bin is = %s"%(PPID_STRING))
				print self.logging("\nPPID is set successfully in opt/dell/mc/conf/infoarea.bin.")
			else:
				print self.logging("\nPPID is fail to set in opt/dell/mc/conf/infoarea.bin.")
				iRet = 'FAIL'
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('PPID_SET_FROM_CONF failed')
			return 'FAIL'
#################################################################################################################
	def Command_Response_Value(self,cmd):
		try:
			self.tn.write(cmd)
			buf=self.tn.read_until('Operation Successful',10)
			self.tn.write('reboot\n')
			print self.logging("wait for 300 sec for MC up and checking property on MCManager ")
			print self.logging("Current time :%s"%(time.ctime()))
			time.sleep(300)
			self.login_to_MC()
			self.tn.write("CLI\n")
			self.tn.write("ls /mcmanager\n")
			self.tn.write("exit\n")
			buf=self.tn.read_until('Exit the Session',10)
			PPID = self.parse_response_property(buf,'PPID = ')
			return PPID
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))	
			raise RuntimeError('Command_Response_Value failed')
			return 'FAIL'
#################################################################################################################
	def Command_Response_Value(self,cmd):
		try:
			self.tn.write(cmd)
			buf=self.tn.read_until('Operation Successful',10)
			self.tn.write('reboot\n')
			print self.logging("wait for 300 sec for MC up and checking property on MCManager ")
			print self.logging("Current time :%s"%(time.ctime()))
			time.sleep(300)
			self.login_to_MC()
			self.tn.write("CLI\n")
			self.tn.write("ls /mcmanager\n")
			self.tn.write("exit\n")
			buf=self.tn.read_until('Exit the Session',10)
			PPID = self.parse_response_property(buf,'PPID = ')
			return PPID
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))	
			raise RuntimeError('Command_Response_Value failed')
			return 'FAIL'
#################################################################################################################
	def PPID_SET(self, string_ppid):
		iRet = 'PASS'
		try:
			print self.logging("\n-------------------------------------------------------------------")
			print self.logging("|                     Set PPID operation start                    |")
			print self.logging("-------------------------------------------------------------------")
			self.login_to_MC()
			time.sleep(3)
			cmd = 'set_ppid '+string_ppid+'\n'
			PPID = self.Command_Response_Value(cmd)
			print self.logging("\nPPID found on CLI is = %s"%(PPID))
			if PPID != string_ppid:
				print self.logging("Failed to set PPID.")
				iRet = 'FAIL'
			else:
				print self.logging("\nPPID set successfully.")
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('PPID_SET failed')
			return 'FAIL'
#################################################################################################################
	def SET_PPID_TEST(self, MC_IP, loop_count = '', UserName = '', Password = ''):
		str1 = "MC1_9876543210"
		str2 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz_12345678910'
		iRet_Final ='PASS'
		try:
			if MC_IP != '':
				self.HOST_IP = MC_IP

			if UserName != '':
				self.user = str(UserName)

			if Password != '':
				self.password = str(Password)

			self.create_log_folder(self.log_file)
			self.check_ping()
			debug = self.debug_mode.lower()
			if debug == "no":
				self.blockPrint()

			count = 1
			if loop_count != '':
				self.loop = loop_count

			self.get_Rack_Info()
			print self.logging("\n*****************************************************************************")
			print self.logging("*                       PPID Test start on %s                     *"%(self.HOST_IP))
			print self.logging("*****************************************************************************")
			old_PPID = self.get_PPID()
			start_count = 1
			for i in range(int(self.loop)):
				iRet = 'PASS'
				str1+=`i`
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n**************************************************")
				print self.logging("*             Test Cycle Number = %s             *"%(start_count))
				print self.logging("**************************************************\n")
				print self.logging("Going to set PPID = %s "%(str1))
				
				PPID_Response1 = self.PPID_SET(str1)
				if PPID_Response1 != 'PASS':
					iRet ='FAIL'
					iRet_Final ='FAIL'
					
				PPID_Response2 = self.PPID_SET_MORE_THAN_64(str2)
				if PPID_Response2 != 'PASS':
					iRet ='FAIL'
					iRet_Final ='FAIL'
				
				PPID_Response3 = self.PPID_SET_FROM_CONF()
				if PPID_Response3 != 'PASS':
					iRet ='FAIL'
					iRet_Final ='FAIL'

				PPID_Response4 = self.PPID_SET_FROM_CONF_MORE_THAN_64()
				if PPID_Response4 != 'PASS':
					iRet ='FAIL'
					iRet_Final ='FAIL'
					
				print self.logging("\n|-------------------------------------------------------------------|")
				print self.logging("|---------------------PPID_Response Test = %s --------------------|"%(iRet))
				print self.logging("|-------------------------------------------------------------------|")
				start_count = start_count + 1

			print self.logging("\n|---------  Going to set for revert back PPID  = %s -----------|"%(old_PPID))
			PPID_Response_revert_back = self.PPID_SET(old_PPID)
			if PPID_Response_revert_back != 'PASS':
				iRet_Final ='FAIL'
				
			print self.logging("\n*****************************************************************************")
			print self.logging("*                          PPID Test result : %s                          *"%(iRet_Final))
			print self.logging("*****************************************************************************\n")
			return iRet_Final
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('SET_PPID_TEST failed')
			return 'FAIL'
#################################################################################################################
if __name__ == "__main__":
    obj=PPID_TEST()
    obj.main(sys.argv[1:])
