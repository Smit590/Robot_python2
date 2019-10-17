import os, sys, time, shutil, re, subprocess
import socket, datetime, telnetlib, getopt
import traceback
import random
#from robot.libraries.BuiltIn import BuiltIn

PASS = 'PASS'
FAIL = 'FAIL'

BC_IpAddress_map = []
Powerbay_Number_map = []
Sled_Bit_map = []
NumberOfBC = ''
NumberOfBC_old =''
Total_Powerbay=''
Total_Powerbay_old =''
totalSleds =''
totalSleds_old =''
Flag = 1
Rack_num_log, current_dir, subdir = ['','','']

#################################################################################################################
####################################Steps followed for this test script##########################################
#################################################################################################################
# 1. Login to MC.
# 2. If login and acquired info is correct start test cycle.
# 3. Modified "RackNumber" Property in /opt/dell/mc/conf/mc.conf file.
# 5. Reboot the MC.Wait for 900 sec for MC boot up.
# 6. After sufficient wait verify all targets with old targets data and return pass if all the targets present.
# 7. For revert back purpose modify racknumber again 1 and follow same process as above.
#################################################################################################################

class Rack_num_change:
	def __init__(self):
		self.tn = None
		self.user = 'root'
		self.password = 'calvin'
		timestr = time.strftime("%Y%m%d-%H%M%S")
		file_name = "Rack_num_change_" + timestr + ".log"
		self.log_file = file_name
		self.loop = '1'
		self.debug_mode = 'yes'
		self.HOST_IP = ''
#################################################################################################################
	def usage(self):
		print "usage : python DSS_test.py"
		print "Common OPTIONS:"
		print "               -h,               --help               -- show Usage, Options"
		print "               -u <user>,        --user=<usernm>      -- username of MC"
		print "               -p <passwd>,      --password=<passwd>  -- password of username"
		print "               -r <rhost>,       --rhost=<rhost>      -- MC IP"
		print "               -f <logfile>,     --file=<logfile>     -- Log filename"
		print "               -l <No.of Test>,  --loop=<No.of Test>  -- No. of test cycle"
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

			self.Rack_num_change('','','')
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
		global Rack_num_log,current_dir,subdir
		try:
			filepath = os.path.join(current_dir, subdir, str(self.HOST_IP), Rack_num_log)
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
	def get_Rack_PowerState(self,racknum_modified):
		start_stop_status = 'NA'
		try:
			self.login_to_MC_for_status()
			self.status.write("CLI\n")
			if (racknum_modified == 'NO'):
				self.status.write("show -d properties=PowerState RACK1\n")
			else:
				self.status.write("show -d properties=PowerState RACK2\n")
			self.status.write("exit\n")
			Response_buf = self.status.read_until('Exit the Session',120)
			self.status.write("exit\n")
			start_stop_status = self.parse_response_property(Response_buf,'PowerState = ')
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Rack_PowerState failed')
		return start_stop_status

#################################################################################################################
	def get_Powerbay_number(self,racknum_modified):
		global Powerbay_Number_map
		PSU_Present='0'
		try:
			self.status.write("CLI\n")
			if (racknum_modified == 'NO'):
				self.status.write('show -d properties=NumberOfPSU,PowerBayNumber Rack1/PowerBay*\n')
			else:
				self.status.write('show -d properties=NumberOfPSU,PowerBayNumber Rack2/PowerBay*\n')
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
	def get_Total_Sleds(self,racknum_modified):
		Count = 0
		try:
			self.status.write("CLI\n")
			if (racknum_modified == 'NO'):
				self.status.write('show -d properties=PresenceState Rack1/Block*/Sled*\n')
			else:
				self.status.write('show -d properties=PresenceState Rack2/Block*/Sled*\n')
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
	def get_BC_IpAddress(self,racknum_modified):
		try:
			self.status.write('CLI\n')
			if (racknum_modified == 'NO'):
				self.status.write('show -d properties=IpAddress Rack1/block*/BC\n')
			else:
				self.status.write('show -d properties=IpAddress Rack2/block*/BC\n')
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
	def Rack_target_number(self):
		try:
			count = 0
			self.login_to_MC_for_status()
			self.status.write('CLI ls\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			print self.logging("BUF: %s " % buf)
			for line in buf.splitlines():
				if (line.find('Rack')!= -1):
					count = count +1
			print self.logging("count: %s " % count)
			return count
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('Rack_target_number failed')
			return 'FAIL'
#################################################################################################################
	def IM_Present(self,racknum_modified):
		try:
			iRet = 'FAIL'
			self.status.write('CLI\n')
			if (racknum_modified == 'NO'):
				self.status.write('show -d properties=PresenceState Rack1/powerbay1/im\n')
			else:
				self.status.write('show -d properties=PresenceState Rack2/powerbay1/im\n')
			self.status.write("exit\n")
			buf = self.status.read_until('Exit the Session',120)
			for line in buf.splitlines():
				if 'PresenceState = ' in line:
					value = line.split()[-1]
					value = value.split('.')[-1]
					if (value == "PRESENT"):
						print self.logging("IM is Present here \n")
						iRet = 'PASS'
						return iRet
			return iRet
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_BC_IpAddress failed')
			return 'FAIL'
#################################################################################################################
	def get_Rack_Info(self,racknum_modified):
		iRet='PASS'
		global Powerbay_Number_map,BC_IpAddress_map,Total_Powerbay_old,NumberOfBC_old,totalSleds_old, Total_Powerbay, NumberOfBC, totalSleds,Flag
		NumberOfBC = 0
		try:
			Powerbay_Number_map = []
			BC_IpAddress_map = []
			print self.logging("\n*****************************************")
			if(racknum_modified == 'NO'):
				print self.logging("MC IpAddress           = %s"%(self.HOST_IP))

				MC_FW_Version = self.get_FW_Version("/MCManager")
				print self.logging("MC Firmware Version    = %s"%(MC_FW_Version))

			isRackPowerON = self.get_Rack_PowerState(racknum_modified)
			print self.logging("Rack Power State       = %s"%(isRackPowerON))
			self.login_to_MC_for_status()
			self.get_Powerbay_number(racknum_modified) 
			Total_Powerbay = Powerbay_Number_map.__len__()
			print self.logging("Total PowerBay Present = %s"%(Total_Powerbay))
			
			self.get_BC_IpAddress(racknum_modified)
			NumberOfBC = BC_IpAddress_map.__len__()
			totalSleds = self.get_Total_Sleds(racknum_modified)
			if(Flag == 1):
				Total_Powerbay_old = Total_Powerbay
				NumberOfBC_old = NumberOfBC
				totalSleds_old = totalSleds
			Flag = Flag +1
			print self.logging("Total Blocks Presence  = %s"%(NumberOfBC))
			print self.logging("Total Sleds Presence   = %s"%(totalSleds))
			if(racknum_modified == 'NO'):
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
	def create_log_folder(self,log_files):
		global Rack_num_log,current_dir,subdir
		try:
			current_dir = os.path.dirname(os.path.realpath(__file__))
			subdir = "../logs"

			if not os.path.exists(current_dir+"/"+subdir):
				os.mkdir(os.path.join(current_dir, subdir))

			if not os.path.exists(current_dir+"/"+subdir+"/"+str(self.HOST_IP)):
				os.mkdir(os.path.join(current_dir, subdir,str(self.HOST_IP)))

			Rack_num_log = log_files
			New_Rack_num_log = current_dir + "/" + subdir + "/" + str(self.HOST_IP) + "/" + Rack_num_log
			old_Rack_num_log = New_Rack_num_log+"_old"

			if os.path.exists(old_Rack_num_log):
				os.remove(old_Rack_num_log)

			if os.path.exists(New_Rack_num_log):
				os.rename(New_Rack_num_log,old_Rack_num_log)

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('create_log_folder failed')
		else:
			print self.logging("\ncreate %s successfully"%(New_Rack_num_log))
			#~ print self.logging("\ncreate ./logs/%s/%s successfully"%(self.HOST_IP,log_files))
#################################################################################################################
	def telnet_login_to_mc(self):
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

#################################################################################################################
	def Rack_num_modify(self):
		try:
			rackno=random.randint(1,99)
			#print self.logging("Rack number will set as : %s " %(rackno))
			iRet ='PASS'
			cmd = 'sed -i \'/RackNumber/s/1/2/g\' /opt/dell/mc/conf/mc.conf'
			self.tn.write(cmd +'\n')
			time.sleep(2)
			self.tn.write('reboot\n')
			print self.logging("Please wait 900 sec to make sure all blocks and sleds are present\n")
			print self.logging("Current time :%s"%(time.ctime()))
			time.sleep(900)
			print self.logging("Loging to MC after reboot")
			print self.logging("Current time :%s"%(time.ctime()))
			self.login_to_MC_for_status()
			iRet = self.verify_targets('YES')
			if (iRet == 'PASS'):
				print self.logging("All targets are present after changing rack number")
			return iRet

		except RuntimeError:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			print self.logging("Failed to Rack_num_modify")
			return 'FAIL'
#################################################################################################################
	def verify_targets(self,racknum_modified):
		try:
			iRet = 'PASS'
			print self.logging("\n------------------------------------")
			print self.logging("|   verifying all targets     |")
			print self.logging("------------------------------------")
			self.get_Rack_Info(racknum_modified)
			self.login_to_MC_for_status()
			IM_PRESENT = self.IM_Present(racknum_modified)
			if( IM_PRESENT != 'PASS'):
				iRet = 'FAIL'
				print self.logging("IM is not present ")
				
			if(NumberOfBC_old != NumberOfBC):
				print self.logging("Number of blocks are not match after changed rack number\n")
				iRet = 'FAIL'
				
			if(Total_Powerbay_old != Total_Powerbay):
				print self.logging("Number of PowerBays are not match after changed rack number\n")
				iRet = 'FAIL'
				
			if(totalSleds_old != totalSleds):
				print self.logging("Number of sleds are not match after changed rack number\n")
				iRet = 'FAIL'
				
			print self.logging("Going to make sure on CLI there are not any extra rack target\n")
			Total_rack = self.Rack_target_number()
			if (Total_rack != 1):
				print self.logging("On CLI there are multiple Rack target\n")
				iRet = 'FAIL'
			return iRet

		except RuntimeError:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			print self.logging("Failed to vverify_targetss")
			return 'FAIL'
#################################################################################################################
	def	Rack_num_change(self,MC_IP, loop_count = '', UserName = '', Password = ''):

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

		iRet = FAIL
		iRet_final = 'PASS'
		if loop_count != '':
			self.loop = loop_count
		try:
			self.get_Rack_Info('NO')
			print self.logging("\n************************************************************************************")
			print self.logging("*           Testing Rack_num_change test start on : %s            *"%(self.HOST_IP))
			print self.logging("************************************************************************************\n")
			
			start_count = 1
			while (start_count <= int(self.loop)):
				self.telnet_login_to_mc()
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n*******************************************************************************")
				print self.logging("*                             Test Cycle Number = %s                          *"%(start_count))
				print self.logging("*******************************************************************************\n")
				iRet = self.Rack_num_modify()
				
				if(iRet == 'FAIL'):
					iRet_final ='FAIL'
					
				print self.logging("****************************************************************************")
				print self.logging("*                 Revert back rack number as 1                          *")
				print self.logging("*****************************************************************************")
				self.telnet_login_to_mc()
				
				cmd = 'sed -i \'/RackNumber/s/2/1/g\' /opt/dell/mc/conf/mc.conf'
				self.tn.write(cmd +'\n')
				time.sleep(2)
				self.tn.write('reboot\n')
				print self.logging("Please wait up to 900 sec\n")
				print self.logging("Current time :%s"%(time.ctime()))
				time.sleep(900)
				print self.logging("After revert back varifying all target again..\n")
				iRet = self.verify_targets('NO')
				if (iRet == 'FAIL'):
					iRet_final ='FAIL'
				start_count = start_count + 1
			print self.logging("********************************************************")
			print self.logging("*                 Rack number change Test : %s                  *"%(iRet_final))
			print self.logging("********************************************************")
			return iRet_final
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError("Rack_num_change_test_fun failed!!")
			return 'FAIL'
#################################################################################################################

if __name__ == "__main__":
    obj=Rack_num_change()
    obj.main(sys.argv[1:])
