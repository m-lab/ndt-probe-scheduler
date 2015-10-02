# ndt-probe-scheduler

As currently implemented, the NDT Probe Scheduler is a generic python script 
that is intended to serve as the scheduling "governor" for an arbitrary 
number of satellite devices.  The IP addresses of the satellite devices
must be statically assigned, and recorded in the in the [Probes]->addresses
section of governer.cfg.  

The other fields in governor.cfg specify the time windows within which tests 
should be run, how many tests should be run (per device) per time window, and 
what the minimum period of time between one test run and the next can be.  

The script uses these parameters to calculate semi-random run times (that meet
all specified parameters) at the start of each time window, and loads them 
into a python scheduler structure.  Whenever any particular run time is reached,
the governor directs the appropriate probe to initiate a test over ssh.  

For example, the configuration shown in the default governor.cfg will result in
3 tests being run from each of 0.0.0.0, 1.1.1.1, and 2.2.2.2, each at least 2
minutes apart from the tests before and afer it (for a total of 9 tests, 
requiring at least 27 minutes).  

Design Notes

In a server/client model, we should have each client exclusively pull config
info from the server (so that the probes can be set up on private IPs). 
The only information that needs to be sent to the server by any given probe is 
the probe's unique ID. The only info that needs to be sent back to each probe 
is the time of the probe's next test run. The client code should wait until 
that time occurs, run a test, and then immediately contact the server to 
request the next test run time.  A very handy extension would be for the 
server to have some sort of alerting mechanism for sending an email if 3 
consecutive run times elapse without a given probe having contacted the server

The Probes section of the governor config file will have to be replaced with a 
list of unique client IDs, which will also need to be manually assigned to each
probe in client-side config files. There should be a separate server-side 
config file for each school. All of them can be handled by the same server 
process, which will load all .cfg files in particular directory whenever
it launches.  

The client-side config files should only need unique IDs, and the URL of the 
governor server.  

The client process should periodically run some sort of NTP check to make sure
that its local clock is correct. The client process should also be responsible
for running get\_ndt\_server, so that the result returned by mlab-ns reflects
the location of the probes, not the governor server.  

The client process should be protected by some sort of wrapper or status 
checker -- perhaps a script in /etc/cron.hourly that makes sure that the client
process is running, and automatically starts it if it isn't.  

