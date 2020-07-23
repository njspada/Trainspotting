# Script to gather log data and push to Google Sheet

#require(tidyverse)
require(dplyr)
library(DBI)
library(RMariaDB)
#require(googledrive)

mysql_user = "dhawal"
mysql_pw = "april+1Hitmonlee"
mysql_db_trainspotting = "trainspotting"
mysql_db_weewx = "weewx"
mysql_host = "localhost"

keyLoc <- paste0("/usr/local/controller/setup/reporting/",
		 "Trainspotting-de6353d6caf4.json")

#drive_auth(path = keyLoc)

#td <- drive_find(team_drive = "Trainspotting")$id

out.dir <- "/mnt/p1/output/"

# Get latest upload date
get_latest <- function() {
  reported <- readLines(paste0(out.dir, 'reporting.log'))
  last <- tail(reported, 1)
  latest <- as.Date(unlist(strsplit(last, "T"))[1], format = "%Y%m%d")
  return(latest)
}

update_latest <- function() {
  line <- format(Sys.time(), format = "%Y%m%dT%H%M")
  write(line, file = paste0(out.dir, 'reporting.log'),
        append=TRUE)
}

# Functions for collecting and processing log data
# Each daily file will contain one second data (86,400 sec/day)
# Each log file will be converted into this one second format
# then all combined
get_met <- function(day) {
  # First setup a connection to the 'archive' table in database 'weewx'
  startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                            format = '%Y-%m-%d %H:%M:%S')
  endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                          format = '%Y-%m-%d %H:%M:%S')
  startTime <- as.numeric(startTime)
  endTime <- as.numeric(endTime)


  weewx_db_con <- dbConnect(RMariaDB::MariaDB(),
                        user = mysql_user,
                        password = mysql_pw,
                        dbname = mysql_db_weewx,
                        host= mysql_host)
  query <- paste("SELECT dateTime,outTemp,outHumidity,rain,
          windSpeed,windDir,windGust,windGustDir,inTemp
          FROM archive 
          WHERE dateTime >=", startTime, 
          "AND dateTime < ", endTime, 
          "ORDER BY dateTime ;")

  res <- dbSendQuery(weewx_db_con, query)
  met <- dbFetch(res) %>%
          mutate_all(~replace(., is.na(.), 0.0))
  met.out <- data.frame(
      dateTime = seq(startTime, endTime)) %>%
      left_join(met, 'dateTime') %>%
      fill(outTemp:inTemp, .direction = 'down') %>%
      fill(outTemp:inTemp, .direction = 'up')
    
  dbDisconnect()
  return(met.out)
}

expand_event <- function(events, eventStart) {
  
  event <- subset(events, startEvent == eventStart)[1,]
  
  event.expanded <- data.frame(
    datetime = seq.POSIXt(event$startEvent, event$endEvent, '1 sec')) %>%
    mutate(TrainDetected = 1)
  
  return(event.expanded)
}

get_camera <- function(day) {
  
  fname <- paste0(out.dir, "camera_", format(day), ".log")
  
  if (file.exists(fname)) {
    
    camera.names <- c('detects', 'startEvent', 'endEvent')
    
    camera <- read.csv(fname,
                       header = F, stringsAsFactors = F,
                       col.names = camera.names) %>%
      mutate(startEvent = as.POSIXct(startEvent, format = "%Y-%m-%dT%H:%M:%S"),
             endEvent = as.POSIXct(endEvent, format = "%Y-%m-%dT%H:%M:%S"),
             TrainDetected = ifelse('train' %in% unlist(strsplit(detects, '_')),
                                    1, 0)) %>%
      filter(TrainDetected == 1)
    
    # For each event, expand out to one second resolution
    camera.expanded <- do.call(
      'rbind',
      lapply(camera$startEvent, function(x) expand_event(camera, x))) %>%
      distinct()
    
    # Initialize one second data frame, join with met, then fill down
    startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                            format = '%Y-%m-%d %H:%M:%S')
    endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                          format = '%Y-%m-%d %H:%M:%S')
    camera.out <- data.frame(
      datetime = seq.POSIXt(startTime, endTime, '1 sec')) %>%
      left_join(camera.expanded, 'datetime') %>%
      mutate(TrainDetected = ifelse(is.na(TrainDetected), 0, 1))
    
    return(camera.out)
    
  }
  return(NULL)
}

get_pa <- function(day) {
  
  fname <- paste0(out.dir, "purpleair_", format(day), ".log")
  
  if (file.exists(fname)) {
    
    pa.names <- c('datetime', 'datetime2', 'mac', 'firmware', 'hardware',
                  'tempF', 'rh', 'dewptF', 'pres', 'adc', 'mem', 'rssi',
                  'uptime',
                  'pm1', 'pm2.5', 'pm10',
                  'pm1_cf', 'pm2.5_cf', 'pm10_cf', # V19
                  'junk1', 'junk2', # V21
                  'p0.3', 'p0.5', 'p1', 'p2.5', 'p5', 'p10', # V27
                  'pm1_b', 'pm2.5_b', 'pm10_b',
                  'pm1_cf_b', 'pm2.5_cf_b', 'pm10_cf_b', # V33
                  'junk3', 'junk4',
                  'p0.3_b', 'p0.5_b', 'p1_b', 'p2.5_b', 'p5_b', 'p10_b',
                  'junk5')
    
    pa <- read.csv(fname,
                   header = F, stringsAsFactors = F,
                   col.names = pa.names) %>%
      # Grab only the fields we're interested in
      select(datetime,
             pm1, pm2.5, pm10,
             p0.3, p0.5, p1, p2.5, p5, p10,
             pm1_b, pm2.5_b, pm10_b,
             p0.3_b, p0.5_b, p1_b, p2.5_b, p5_b, p10_b) %>%
      mutate(datetime = as.POSIXct(datetime, format = "%Y-%m-%d %H:%M:%S")) %>%
      # Wrangle the data into a long form we can use to compare the two channels
      gather(Tmp, Value, pm1:p10_b) %>%
      separate(Tmp, c('Type', 'Channel'), sep = '_', fill = 'right') %>%
      mutate(Channel = ifelse(is.na(Channel), 'a', Channel)) %>%
      spread(Channel, Value) %>%
      # Calculate the mean value between the two sensors and 
      # the scaled relative difference
      mutate(Mean = (a + b) / 2,
             SRD = ( (a - b) / sqrt(2) ) / Mean)
    
    # We will only accept results where the PM2.5 estimate is within +/- 0.5
    # for he SRD
    good <- select(pa, datetime, SRD) %>%
      filter(SRD >= -0.5 | SRD <= 0.5) %>%
      .$datetime
    
    # Prepare dataset for return
    pa.abr <- pa %>%
      filter(datetime %in% good) %>%
      select(datetime, Type, Mean) %>%
      spread(Type, Mean) %>%
      select(datetime, pm2.5, pm1, pm10, p0.3, p0.5, p1, p2.5, p5, p10)
    
    # Initialize one second data frame, join with met, then fill down
    startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                            format = '%Y-%m-%d %H:%M:%S')
    endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                          format = '%Y-%m-%d %H:%M:%S')
    pa.out <- data.frame(
      datetime = seq.POSIXt(startTime, endTime, '1 sec')) %>%
      left_join(pa.abr, 'datetime') %>%
      fill(pm2.5:p10, .direction = 'up') %>%
      fill(pm2.5:p10, .direction = 'down')
    
    return(pa.out)
    
  }
  return(NULL)
}

get_logs <- function(day) {
  
  # Collect and process log files
  met <- get_met(day = day)
  camera <- get_camera(day = day)
  pa <- get_pa(day = day)
  
  if (!is.null(met) & !is.null(camera) & !is.null(pa)) {
    # Combine into final dataset
    total <- met %>%
      left_join(camera, 'datetime') %>%
      left_join(pa, 'datetime')
    
    return(total)
  }
  return(data.frame())
}

# Function to gather/process logs, then upload
report_daily <- function(day) {
  
  # Collect and process log files for the day
  total <- get_logs(day = day)
  
  if (nrow(total) > 0) {
    
    fname <- paste0('daily_', format(day), '.csv')
    fpath <- paste0(out.dir, 'gDriveSync/', fname)
    write.csv(total, fpath, row.names = F)
    
    # Now upload file to Google Drive
    #drive_upload(fpath, path = as_id(td))
  }
}


# Main function to run reporting service at appropriate time
run_service <- function() {
  
  # Upload the daily file at 5 minutes before midnight each day
  # this avoids the polling of the met data
  
  running <- T
  
  while (running == T) {

    now <- Sys.time()
    
    if (format(now, "%H%M") == '2355') {
      
      # Figure out which days still need reported
      latest <- get_latest()
      today <- Sys.Date()
      days2report <- seq.Date(latest + 1, today - 1, 1)
      
      # For each day, combine files and upload
      lapply(days2report, report_daily)
      
      update_latest()
      
    } else {
      
      # Sleep for 10 seconds
      Sys.sleep(1)
      
    }
  }
}


# run_service()
