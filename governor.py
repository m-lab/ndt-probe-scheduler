import sched, time, random, ConfigParser, subprocess, json, urllib2
config = ConfigParser.RawConfigParser()

test_duration=35
last_run=0

governor = sched.scheduler(time.time, time.sleep)

   #This function should always be run from the network on which the probes are located.  
def get_ndt_server():
   mlabns=urllib2.urlopen('http://mlab-ns.appspot.com/ndt')
   server = dict(json.loads(mlabns.read()))['fqdn'].encode('ascii')
   return server

def run_ndt (addr):
   ndt_server = get_ndt_server()
   ndt_cmd="web100clt -n " + ndt_server + " --disablesfw --disablemid"
   print "Running test on device " + addr + " at " + time.strftime("%x,%H:%M:%S")
   test_output = subprocess.Popen(["ssh", addr, ndt_cmd],stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
   log_text = test_output.communicate()
   logfile = open(addr + ".log", 'a')
   logfile.write(time.strftime("\n-------\n%x,%H:%M:%S\n" + ndt_server + "\n"))
   for line in log_text[0].split('\n'):
      print line
      logfile.write(line + "\n")
   logfile.close()
   # This will only work if the SSH infrastucture on the governor and the probes
   # has been set up correctly. If/when this code is restructed into server and 
   # client components, this code will have to be largely scrapped


while True:
   #Initialize time, and read config file
   now = time.localtime()
   if last_run < now:
      last_run = now
   config.read("beta.cfg")
   probes_to_run = config.get("Probes", "addresses").split()
   interval = int(config.get("Timing", "delay"))*60
   runs_per_period = int(config.get("Timing", "runs_per_period"))

   # Assemble the list of today's period boundaries by mashing together today's 
   # date and the generic hour:minute entries from the config file
   period_boundaries = [time.strptime(time.strftime("%x", now) + "," + t, "%x,%H%M") for t in config.get("Timing", "boundaries").split()]

   #Identify the next (upcoming) period boundary
   for next_period in period_boundaries:
      if next_period > now:
         if last_run < next_period: #WRONG.  Also, you need to add the frequency
#            print str(last_run) + ", " + str(next_period)
            break

   #If we get to the end of the list of period boundaries and nothing is in the future, roll over to the next day, and use the first period boundary in the config file
   #TODO: This logic will break at the day boundary at the end of a leapyear, when %j will be incremented to 367, which is out of the range "time" accepts 
   else:
      next_period = time.strptime(str(now.tm_year) + "," + str(now.tm_yday+1) + "," + config.get("Timing", "boundaries").split().pop(0), "%Y,%j,%H%M")
      #TODO:Should we sort the boundary list before blindly grabbing the first element?

   #Sanity check to make sure that the parameters specified in the config file are possible to implement in the current time window
   #TODO: This will break if the governor is launched shortly befor the next time boundary.  Perhaps just skip to the next time boundary in that case, and bail only if the parameters also prove impossible to implement in that next window?
   if time.mktime(now) + runs_per_period*(test_duration+((len(probes_to_run)-1)*(test_duration+interval))) > time.mktime(next_period):
      raise RuntimeError("Specified test delay is too long, and/or specified periods are too short, to accomidate the number of devices.")
   else:
      max_gap = ((time.mktime(next_period) - time.mktime(now)) - (runs_per_period*(test_duration+((len(probes_to_run)-1)*(test_duration+interval)))))/runs_per_period
      print max_gap
   for i in range(0, runs_per_period):
      print last_run
      start_time = time.mktime(last_run) + random.randint(1, int(max_gap))
      #start_time = random.randint(time.mktime(last_run), (time.mktime(next_period)-(test_duration+((len(probes_to_run)-1)*(test_duration+interval)))))
      random.shuffle(probes_to_run)
      counter=0
      for probe in probes_to_run:
         print "Running test on device " + probe + " at " + time.strftime("%x,%H:%M:%S",time.localtime(start_time+counter*interval))
         governor.enterabs(start_time+(counter*(test_duration+interval)),1,run_ndt,[probe])
         counter=counter+1
      last_run = time.localtime(start_time + (test_duration+((len(probes_to_run)-1)*(test_duration+interval))))
#   if time.mktime(now) + (test_duration+((len(probes_to_run)-1)*(test_duration+interval))) > time.mktime(next_period):
#      raise RuntimeError("Specified test interval is too long, and/or specified periods are too short, to accomidate the number of devices.")
#   start_time = random.randint(time.mktime(last_run), (time.mktime(next_period)-(test_duration+((len(probes_to_run)-1)*(test_duration+interval)))))
#   random.shuffle(probes_to_run)
#   counter=0
#   for probe in probes_to_run:
#      print "Running test on device " + probe + "at " + time.strftime("%x,%H:%M:%S",time.localtime(start_time+counter*interval))
#      governor.enterabs(start_time+(counter*(test_duration+interval)),1,run_ndt,[probe])
#      counter=counter+1
   last_run=next_period
   governor.run()   
