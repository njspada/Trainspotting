# Script to gather log data and push to Google Sheet

require(tidyverse)
#require(dplyr)
require(DBI)
require(RMariaDB)
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

out.dir <- "/Desktop/output/logs/"
post_url <- "192.168.10.120"
images_dir <- "Desktop/output/"

save_da <- function(da, day) {
	# 1. save each dataframe in a csv file
	# 2. upload/post each csv file to cloud
	# 3. upload/post each image from train_images to cloud
	post_df <- function(df, fpath, fname, type) {
		body = list(type=type, file=upload_file(fpath), device_id="0", filename=fname, tablename=type)
		POST(post_url, body=body, encode"multipart")
	}
	save_df <- function(df, name) {
		fname <- paste0('daily_', format(day), '.csv')
    	fpath <- paste0(out.dir, fname)
    	write.csv(df, fpath, row.names = F)
    	return(list(fpath=fpath, fname=fname))
	}
	da_file <- save_df(da$da, "daily_aggregate")
	train_detects_file <- save_df(da$train_detect, "train_detects")
	train_images_file <- save_df(da$train_images, "train_images")

	post_df(da$da, da_file$fpath, da_file$fname, "da")
	post_df(da$train_detect, train_detects_file$fpath, train_detects_file$fname, "train_detects")
	post_df(da$train_images, train_images_file$fpath, train_images_file$fname, "train_images")
	
	post_image <- function(filename) {
		body = list(type="image", file=upload_file(paste(images_dir,filename)), device_id="0", filename=filename)
		POST(post_url, body=body, encode="multipart")
	}

	sapply(da$train_images$filename, post_image)
}

pipe_print = function(data) {print(tail(data)); data}

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
    
  dbClearResult(res)
  dbDisconnect(weewx_db_con)
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

	# return 3 data frames - 
	# 1. train_events - timestamp sequence with event id for every second. (event_id=-1 for no event)
	# 		Also add columns `is_stat` and `is_moving`.
	# 2. train_detetcs - exact copy of the sql table `train_detects`
	# 3. train_images - exact copy of the sql table `train_images`


	startTime <- as.POSIXct(paste(format(day), '00:00:00'))
                            # format = '%Y-%m-%d %H:%M:%S')
    endTime <- as.POSIXct(paste(format(day), '23:59:59'))
                          # format = '%Y-%m-%d %H:%M:%S')
	startTime <- as.numeric(startTime)
  	endTime <- as.numeric(endTime)
  	# print(startTime)
  	# print(endTime)
  	timestamp_seq <- data.frame(dateTime = seq(startTime, endTime))

  	train_db_con <- dbConnect(RMariaDB::MariaDB(),
			                user = mysql_user,
			                password = mysql_pw,
			                dbname = mysql_db_trainspotting,
			                host= mysql_host)

  	# first get all train events - event_id, start_time, end_time
	# then create a timestamp sequence for the whole day by seconds
	# then create a sequence of train events - (start_time,end_time,event_id) -> [(start_time,event_id),(start_time+1,event_id),...,(end_time,event_id)]
	# and then left join train events to timestamp sequence
  	query <- paste("SELECT *
  			FROM train_events
  			WHERE start >= ", startTime, 
  			"AND end <= ", endTime, ";")

  	res <- dbSendQuery(train_db_con, query)
  	train_events <- dbFetch(res) %>%
  					pipe_print() %>%
  					pmap_df(~data.frame(dateTime=seq(..2,..3), event_id=..1)) %>%
  					# pipe_print() %>%
  					mutate(event_id = ifelse(is.na(event_id), -1, event_id)) %>%
  					group_by(dateTime) %>%
  					summarize(event_id = min(event_id), .groups = 'drop')

  	start_event_id <- head(train_events,1)$event_id
  	end_event_id <- tail(train_events,1)$event_id
  	train_events <- timestamp_seq %>%
  					left_join(train_events, "dateTime") %>%
  					mutate(event_id = ifelse(is.na(event_id), -1, event_id))

  	# now fetch train_detects, and transform that
  	query <- paste("SELECT *
  			FROM train_detects
  			WHERE event_id >= ", start_event_id, 
  			"AND event_id <= ", end_event_id, ";")
  	res <- dbSendQuery(train_db_con, query)
  	train_detects <- dbFetch(res)
  	train_detect_for_events <- select(train_detects, event_id, type)

  	# add `is_stat` to train_events
  	train_events <- train_events %>%
  					left_join(subset(train_detect_for_events, type == 2), 'event_id') %>%
  					mutate(type = ifelse(is.na(type), -1, type)) %>%
  					mutate(is_stat = ifelse(type == 2, TRUE, FALSE)) %>%
  					select(-type)

  	# add `is_moving` to train events
  	train_events <- train_events %>%
  					left_join(subset(train_detect_for_events, type == 1), 'event_id') %>%
  					mutate(type = ifelse(is.na(type), -1, type)) %>%
  					mutate(is_moving = ifelse(type == 1, TRUE, FALSE)) %>%
  					select(-type)

  	train_events <- train_events[!duplicated(train_events$dateTime), ]

  	query <- query <- paste("SELECT *
  			FROM train_images
  			WHERE event_id >= ", start_event_id, 
  			"AND event_id <= ", end_event_id, ";")
  	# print(paste("start_event_id=", start_event_id))
  	# print(paste("end_event_id=", end_event_id))
  	res <- dbSendQuery(train_db_con, query)
  	train_images <- dbFetch(res)

  	rvalue <- list("train_events_da" = train_events, "train_detects" = train_detects, "train_images" = train_images)

  	return(rvalue) # also return train_detects, train_images
}

get_pa_data <- function(day) {
  startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                            format = '%Y-%m-%d %H:%M:%S')
  endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                          format = '%Y-%m-%d %H:%M:%S')
  startTime <- as.numeric(startTime)
  endTime <- as.numeric(endTime)


  pa_db_con <- dbConnect(RMariaDB::MariaDB(),
                        user = mysql_user,
                        password = mysql_pw,
                        dbname = mysql_db_trainspotting,
                        host= mysql_host)
  query <- paste("SELECT *
          FROM purple_air 
          WHERE dateTime >=", startTime, 
          "AND dateTime < ", endTime, 
          "ORDER BY dateTime ;")

  res <- dbSendQuery(pa_db_con, query)
  pa <- dbFetch(res)
  return(pa)
}

get_pa <- function(day) {

  startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                            format = '%Y-%m-%d %H:%M:%S')
  endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                          format = '%Y-%m-%d %H:%M:%S')
  startTime <- as.numeric(startTime)
  endTime <- as.numeric(endTime)


  pa_db_con <- dbConnect(RMariaDB::MariaDB(),
                        user = mysql_user,
                        password = mysql_pw,
                        dbname = mysql_db_trainspotting,
                        host= mysql_host)
  query <- paste("SELECT *
          FROM purple_air 
          WHERE dateTime >=", startTime, 
          "AND dateTime < ", endTime, 
          "ORDER BY dateTime ;")

  res <- dbSendQuery(pa_db_con, query)
  pa <- dbFetch(res) %>%
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
  good <- select(pa, dateTime, SRD) %>%
    filter(SRD >= -0.5 | SRD <= 0.5) %>%
    .$dateTime
  
  # Prepare dataset for return
  pa.abr <- pa %>%
    filter(dateTime %in% good) %>%
    select(dateTime, Type, Mean) %>%
    spread(Type, Mean) %>%
    select(dateTime, pm1, pm2.5, pm10, p0.3, p0.5, p1, p2.5, p5, p10)
  
  # Initialize one second data frame, join with met, then fill down
  pa.out <- data.frame(
    dateTime = seq(startTime, endTime)) %>%
    left_join(pa.abr, 'dateTime') %>%
    fill(pm1:p10, .direction = 'down') %>%
    fill(pm1:p10, .direction = 'up')
  
  dbClearResult(res)
  dbDisconnect(pa_db_con)
  return(pa.out)
}

get_logs <- function(day) {
  
  # Collect and process log files
  met <- get_met(day = day)
  camera <- get_camera(day = day)
  pa <- get_pa(day = day)
  
  if (!is.null(met) & !is.null(camera) & !is.null(pa)) {
    # Combine into final dataset
    da <- met %>%
      left_join(camera$train_events, 'dateTime') %>%
      left_join(pa, 'dateTime')
    
    return(list("da"=da,"train_images"=camera$train_images,"train_detects"=camera$train_detects))
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
