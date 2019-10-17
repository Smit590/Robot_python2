import os, sys, time, shutil, re
import socket, datetime, telnetlib, getopt
import traceback
#from robot.libraries.BuiltIn import BuiltIn

BC_IpAddress_map = []
PowerBay_Num_map = []
Infra_log, current_dir, subdir = ['','','']

#################################################################################################################
####################################Steps followed for this test script##########################################
#################################################################################################################
#1. login to MC.
#2. get the present bc & powerbay map locations.
#3. get rack infrastructure.
#4. now get infrastructure of each im & bc & powerbay present from the map location in step 2. And print each of this property.
#5. In step 3 if rack infrastructure shows 'ERROR' test fails and continue test for number of iterations (defined by user).  

#################################################################################################################

class Infrastructure_Check:
	def __init__(self):
		self.tn = None
		self.IP = None
		self.user = 'root'
		self.password = 'calvin'
		#~ self.log_file = 'Infrastructure_Check.log'
		timestr = time.strftime("%Y%m%d-%H%M%S")
		file_name = "Infrastructure_check_" + timestr + ".log"
		self.log_file = file_name
		self.loop = '1'
		self.debug_mode = 'yes'
		self.HOST_IP = ''
#################################################################################################################
	def usage(self):
		print "usage : python Infrastructure_Check.py"
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

		self.check_Infrastructure('','','')
#################################################################################################################
	def blockPrint(self):
		sys.stdout = open(os.devnull, 'w')
#################################################################################################################
	def logging(self, my_string, time_print = None):
		global Infra_log,current_dir,subdir
		try:
			filepath = os.path.join(current_dir, subdir, str(self.HOST_IP), Infra_log)
			with open(filepath,'a+') as log_file:
				#~ if time_print is not None:
					#~ log_file.write(str(time.ctime()))
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
		global Infra_log,current_dir,subdir
		try:
			current_dir = os.path.dirname(os.path.realpath(__file__))
			print ("current_dir:%s"%current_dir)
			subdir = "../logs"

			if not os.path.exists(current_dir+"/"+subdir):
				os.mkdir(os.path.join(current_dir, subdir))

			if not os.path.exists(current_dir+"/"+subdir+"/"+str(self.HOST_IP)):
				os.mkdir(os.path.join(current_dir, subdir,str(self.HOST_IP)))

			Infra_log = log_files

			New_Infra_log = current_dir + "/" + subdir + "/" + str(self.HOST_IP) + "/" + Infra_log
			old_Infra_log = New_Infra_log+"_old"

			if os.path.exists(old_Infra_log):
				os.remove(old_Infra_log)

			if os.path.exists(New_Infra_log):
				os.rename(New_Infra_log,old_Infra_log)

		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('create_log_folder failed')
		else:
			print self.logging("\ncreate %s successfully"%(New_Infra_log))
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
#################################################################################################################
	def login_to_MC_for_status(self):
		try:
			self.IP = telnetlib.Telnet(self.HOST_IP)

			self.IP.read_until("login: ")
			self.IP.write(self.user + "\n")

			self.IP.read_until("Password: ")
			self.IP.write(self.password + "\n")
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))	
#################################################################################################################
	def get_BC_IpAddress(self):
		try:
			self.IP.write('CLI\n')
			self.IP.write('show -d properties=IpAddress /DeviceManager/Rack1/block*/BC\n')
			self.IP.write("exit\n")
			buf = self.IP.read_until('Exit the Session',120)

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
#################################################################################################################
	def get_PowerBay_Num(self):
		global PowerBay_Num_map
		PSU_Present='0'
		try:
			self.IP.write("CLI\n")
			self.IP.write('show -d properties=NumberOfPSU,PowerBayNumber Rack1/PowerBay*\n')
			self.IP.write("exit\n")
			buf=self.IP.read_until('Exit the Session')
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
						PowerBay_Num_map.append(powerbayno)
					PSU_Present='0'
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('get_Powerbay_number failed')
#################################################################################################################
	def parse_response_property(self, tn_buf):
		infra_value = ''
		try:
			tn_buf_ = str(tn_buf)
			for line in tn_buf_.splitlines():
				if 'Infrastructure = ' in line:
					value = line.split()[-1]
					infra_value = value
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('parse_response_property failed')

		return infra_value
#################################################################################################################
	def get_Infrastructure(self,target_path):
		iRet = 'G5'
		try:
			self.IP.write("CLI\n")
			command = 'show -d properties=Infrastructure ' + str(target_path)
			self.IP.write( str(command) + '\n')
			self.IP.write("exit\n")
			Response_buf = self.IP.read_until('Exit the Session',120)
			iRet = self.parse_response_property(Response_buf)
		except:
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			raise RuntimeError('load_command_execution failed')
		return iRet
#################################################################################################################
	def check_Infrastructure(self, MC_IP, loop_count = '',UserName = '', Password = ''):
		global BC_IpAddress_map,PowerBay_Num_map
		iRet = 'FAIL'
		
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
			
		try:
			print self.logging("\n*****************************************************************")
			print self.logging("*          Infrastructure Test start on %s           *"%(self.HOST_IP))
			print self.logging("*****************************************************************\n")

			#~ self.login_to_MC()
			self.login_to_MC_for_status()

			self.get_BC_IpAddress()
			NumberOfBC = BC_IpAddress_map.__len__()

			self.get_PowerBay_Num()
			NumberOfPowerBay = PowerBay_Num_map.__len__()

			print self.logging("-----------------------------------------------------------------")
			print self.logging("|           Check Rack, PowerBay, LLC's Infrastructure          |")
			print self.logging("-----------------------------------------------------------------\n")
			
			Rack_infrastructure = ''
			start_count = 1
			while (start_count <= int(self.loop)):
				print self.logging("Current time :%s"%(time.ctime()))
				print self.logging("\n*******************************************************************************")
				print self.logging("*                             Test Cycle Number = %s                          *"%(start_count))
				print self.logging("*******************************************************************************\n")
				
				Rack_infrastructure = self.get_Infrastructure('Rack1')
				print self.logging("Rack Infrastructure          = %s"%(Rack_infrastructure))

				for PB_Num in range(NumberOfPowerBay):
					MC1_infrastructure = self.get_Infrastructure('Rack1/PowerBay' + PowerBay_Num_map[PB_Num] + '/MC1')
					print self.logging("PowerBay%s/MC1 Infrastructure = %s"%(PowerBay_Num_map[PB_Num],MC1_infrastructure))

				for BC_Num in range(NumberOfBC):
					Block_infrastructure = self.get_Infrastructure('Rack1/Block' + BC_IpAddress_map[BC_Num])
					print self.logging("Block%s Infrastructure        = %s"%(BC_IpAddress_map[BC_Num],Block_infrastructure))

				IM_infrastructure = self.get_Infrastructure('Rack1/PowerBay1/IM')
				print self.logging("IM Infrastructure            = %s"%(IM_infrastructure))

				if Rack_infrastructure != 'ERROR':
					iRet = 'PASS'

				print self.logging("\n*****************************************************************")
				print self.logging("*                  Infrastructure Test : %s                   *"%(iRet))
				print self.logging("*****************************************************************\n")

				start_count = start_count + 1
			return Rack_infrastructure
		except:
			print 'Interrupt signal or script stopped by user'
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
				print self.logging("Exception from %s line_no: %d fun_name: %s statement: %s " % (fname, lineno, fn, text))
			return 'FAIL'
#################################################################################################################

if __name__ == "__main__":
    obj=Infrastructure_Check()
    obj.main(sys.argv[1:])
