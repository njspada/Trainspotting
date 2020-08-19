import os
import math as m
from datetime import datetime, timedelta
from statistics import mean

# Define functions
def scrape_values(valString):
    if valString.find("None") > 0:
        return 0.0
    return float(valString.split(": ")[1])

def Average(lst):
    return str(round(mean(lst), 1))

def AvgWindDir(v, u):
    return str(round(m.degrees(m.atan2(sum(u), sum(v))), 1))

# Make sure met.txt is empty
with open("/mnt/p1/output/met.txt", "w") as the_file:
    the_file.write('')

# Grab all the data from the met station
myCmd = 'timeout 150s /usr/bin/weewxd /etc/weewx/weewx.conf '
myCmd = myCmd + '| cat >> /mnt/p1/output/met.txt'
os.system(myCmd)

# Now read in the file and collect the most recent data
with open("/mnt/p1/output/met.txt", "r") as the_file:
    metData = the_file.readlines()

### ADD AN IF STATEMENT HERE TO MAKE SURE LINES TO READ
if len(metData) > 1:

    # We will take 10 minute averages
    span = timedelta(minutes = 10)
    endTime = datetime.now()
    #endTime = datetime(2019, 10, 5, 9, 32, 54)
    startTime = endTime - span

    # Initiate lists
    # Note that the wind parameters are separated into vector
    # components, this is so they can be averaged accurately
    temp = []
    rh = []
    ws = []
    wg = []
    windNS = []
    windEW = []
    gustNS = []
    gustEW = []
    rain = []
    inTemp = []

    # Parse each line and gather information
    for line in range(len(metData)):

        # Grab record
        a = metData[line]
        #print(a)

        # First get the timestamp
        aUnix = int(a.split("(")[1].split(")")[0])
        aTime = datetime.fromtimestamp(aUnix)

        # If record is within our window, grab values
        if (aTime >= startTime and aTime <= endTime):

            # Keep this data
            aData = a.split(",")

            # Indices are different based on type (REC vs LOOP)
            # Better to search for each individual than to hardcode
            tempID = [i for i, s in enumerate(aData) if 'outtemp' in s.lower()][0]
            rhID = [i for i, s in enumerate(aData) if 'outhumidity' in s.lower()][0]
            wsID = [i for i, s in enumerate(aData) if 'windspeed:' in s.lower()][0]
            wdID = [i for i, s in enumerate(aData) if 'winddir:' in s.lower()][0]
            wgID = [i for i, s in enumerate(aData) if 'windgust:' in s.lower()][0]
            wgdID = [i for i, s in enumerate(aData) if 'windgustdir:' in s.lower()][0]
            rainID = [i for i, s in enumerate(aData) if 'rain:' in s.lower()][0]
            intempID = [i for i, s in enumerate(aData) if 'intemp:' in s.lower()][0]

            # Get straightforward values
            temp.append(scrape_values(aData[tempID]))
            rh.append(scrape_values(aData[rhID]))
            rain.append(scrape_values(aData[rainID]))
            inTemp.append(scrape_values(aData[intempID]))

            # Now get wind values and calculate vectors
            aWS = scrape_values(aData[wsID])
            wd = scrape_values(aData[wdID])
            aWG = scrape_values(aData[wgID])
            wgd = scrape_values(aData[wgdID])

            windNS.append(m.cos(m.radians(wd)) * aWS)
            windEW.append(m.sin(m.radians(wd)) * aWS)
            gustNS.append(m.cos(m.radians(wgd)) * aWG)
            gustEW.append(m.sin(m.radians(wgd)) * aWG)

            # Append wind and gust speeds to lists
            ws.append(aWS)
            wg.append(aWG)

    # Now that we have our data, it's time to take averages
    tempAvg = Average(temp)
    rhAvg = Average(rh)
    rainAvg = Average(rain)
    wsAvg = Average(ws)
    wdAvg = AvgWindDir(windNS, windEW)
    wgAvg = Average(wg)
    wgdAvg = AvgWindDir(gustNS, gustEW)
    intempAvg = Average(inTemp)


    # Prepare line to write to log file
    outTime = endTime.strftime("%Y%m%dT%H%M%S")
    TODAY = endTime.strftime("%Y-%m-%d")
    out = [outTime, tempAvg, rhAvg, rainAvg, wsAvg, wdAvg, wgAvg, wgdAvg, intempAvg]
    record = ','.join(out)
    record = record + '\n'

    fname = "/mnt/p1/output/met_" + TODAY + ".log"

    # Write the record to the log file and clear out met.txt
    with open(fname, "a") as the_file:
        the_file.write(record)

    with open("/mnt/p1/output/met.txt", "w") as the_file:
        the_file.write('')



        
    

        





