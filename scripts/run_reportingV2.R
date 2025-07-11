# Script to gather log data and push to AWS server

require(tidyverse)
require(DBI)
require(RMariaDB)
require(httr)

source('config/reporting_config.R')



save_df <- function(df, name, day) {
  
  fname <- paste0(name, '/', format(day), '.csv')
  
  fpath <- paste0(dir_logs, fname)
  
  write.csv(df, fpath, row.names = F)
  
  return(list(fpath = fpath, fname = fname))
}


post_df <- function(df, fpath, fname, type) {
  
  # first create a tar ball of the file
  system(paste0('tar -cvzf ',fpath,'.tgz',' ',fpath))
  
  body = list(type = type,
              file = upload_file(paste0(fpath,'.tgz')),
              device_id = device_id,
              filename = fname,
              tablename = type)
  
  r <- POST(post_url, body = body, encode = "multipart")
  # print(content(r,"text"))
  
}


post_image <- function(filename) {
  
  body = list(type = "image",
              file = upload_file(paste0(dir_images, filename)),
              device_id = device_id,
              filename = filename)
  
  r <- POST(post_url, body=body, encode="multipart")
  # print(content(r,"text"))
}


save_da <- function(da, day) {
  
	# 1. save each dataframe in a csv file
	# 2. upload/post each csv file to cloud
	# 3. upload/post each image from train_images to cloud

  # print(nrow(da$da))
	da_file <- save_df(da$da, "daily_aggregate", day = day)
	
	post_df(da$da, da_file$fpath, da_file$fname, "daily_aggregate_v3")
	
	if (nrow(da$train_images) > 0) {
	  
	  train_images_file <- save_df(da$train_images, "train_images", day = day)
	  
	  post_df(da$train_images,
	          train_images_file$fpath,
	          train_images_file$fname, "train_images")
	  
	  sapply(da$train_images$filename, post_image)
	}
	
	if (nrow(da$train_detect) > 0) {
	  
	  train_detects_file <- save_df(da$train_detect, "train_detects", day = day)
	  
	  post_df(da$train_detect, train_detects_file$fpath,
	          train_detects_file$fname, "train_detects")
	
	}
	
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
  # returns dataframe with the following headers (9) - 
  # dateTime,outTemp,outHumidity,rain,windSpeed,windDir,windGust,windGustDir,inTemp

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
  #      headers(4) - dateTime, event_id, is_stat, is_moving
  #     
	# 2. train_detetcs - exact copy of the sql table `train_detects`
  #     headers(10) - id, event_id, type, image_id, label, score, x0, y0, x1, y1
	# 3. train_images - exact copy of the sql table `train_images`
  #     headers(3) -  id, filename, event_id

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
    # table `train_events` has columns - id, start, end

  	res <- dbSendQuery(train_db_con, query)
    # following line mutates train_events to have fields - dateTime, event_id 
  	train_events <- dbFetch(res)
    dbClearResult(res)
    if(nrow(train_events) == 0){
      train_events <- data.frame(rbind(c(-1, startTime, endTime))) # empty frame
    }
    train_events <- train_events %>%
                    pmap_df(~data.frame(dateTime=seq(..2,..3), event_id=..1)) %>%
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
    dbClearResult(res)
  	train_detect_for_events <- select(train_detects, event_id, type)

  	# add `is_stat` to train_events
  	train_events <- train_events %>%
  					left_join(subset(train_detect_for_events, type == 2), 'event_id') %>%
  					mutate(type = ifelse(is.na(type), -1, type)) %>%
  					mutate(is_stat = ifelse(type == 2, 1, 0)) %>% # here 1=TRUE, 0=FALSE
  					select(-type)

  	# add `is_moving` to train events
  	train_events <- train_events %>%
  					left_join(subset(train_detect_for_events, type == 1), 'event_id') %>%
  					mutate(type = ifelse(is.na(type), -1, type)) %>%
  					mutate(is_moving = ifelse(type == 1, 1, 0)) %>% # here 1=TRUE, 0=FALSE
  					select(-type)

  	train_events <- train_events[!duplicated(train_events$dateTime), ]

  	# query <- query <- paste("SELECT *
  	# 		FROM train_images
  	# 		WHERE event_id >= ", start_event_id, 
  	# 		"AND event_id <= ", end_event_id, ";")

    query <- paste("SELECT *
        FROM train_images
        WHERE dateTime >= ", startTime, 
        "AND dateTime <= ", endTime, ";")

  	res <- dbSendQuery(train_db_con, query)
  	train_images <- dbFetch(res) %>% separate(filename, c('remove', 'filename'), sep = 'images/') %>% select(-remove)
    dbClearResult(res)

  	rvalue <- list("train_events" = train_events, "train_detects" = train_detects,
  	               "train_images" = train_images)

  	return(rvalue)
}

get_pa <- function(day) {

  # returns 1 dataframe
  #  headers(10) - dateTime, pm1, pm2.5, pm10, p0.3, p0.5, p1, p2.5, p5, p10

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

get_ra <- function(day) {
  
  # returns 1 dataframe
  # headers(22) - dateTime, p03_a[b,c], p05_a[b,c], p10_a[b,c], p25_a[b,c], p50_a[b,c], p100_a[b,c], pm25_a[b,c]
  
  startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                          format = '%Y-%m-%d %H:%M:%S')
  endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                        format = '%Y-%m-%d %H:%M:%S')
  startTime <- as.numeric(startTime)
  endTime <- as.numeric(endTime)
  
  ra_db_con <- dbConnect(RMariaDB::MariaDB(),
                         user = mysql_user,
                         password = mysql_pw,
                         dbname = mysql_db_trainspotting,
                         host= mysql_host)
  query <- paste("SELECT *
          FROM rugged_air 
          WHERE dateTime >=", startTime, 
                 "AND dateTime < ", endTime, 
                 "ORDER BY dateTime ;")
  
  res <- dbSendQuery(ra_db_con, query)
  ra <- dbFetch(res) 
  
  dbClearResult(res)
  dbDisconnect(ra_db_con)
  return(ra)
}

get_logs <- function(day) {
  
  # returns 3 dataframes - 
  # 1. da (daily_aggregate)
  #  headers(21) - 
  #   from met - dateTime, outTemp, outHumidity, rain, windSpeed,
  #              windDir, windGust, windGustDir, inTemp
  #   from camera - event_id, is_stat, is_moving
  #   from pa - pm1, pm2.5, pm10, p0.3, p0.5, p1, p2.5, p5, p10

  # 2. train_detetcs - exact copy of the sql table `train_detects`
  #     headers(10) - id, event_id, type, image_id, label, score, x0, y0, x1, y1

  # 3. train_images - exact copy of the sql table `train_images`
  #     headers(3) -  id, filename, event_id

  # Collect and process log files
  met <- get_met(day = day)
  camera <- get_camera(day = day)
  ra <- get_ra(day = day)
  
  if (!is.null(met) & !is.null(camera) & !is.null(ra)) {
    
    # Combine into final dataset. Start with a 1 second data frame
    da <- data.frame(
      dateTime = seq.POSIXt(as.POSIXct(paste(day, '00:00:00')),
                            as.POSIXct(paste(day, '23:59:59')),
                            1)) %>%
      mutate(dateTime = as.numeric(dateTime)) %>%
      left_join(met, 'dateTime') %>%
      left_join(ra, 'dateTime') %>%
      left_join(camera$train_events, 'dateTime') %>%
      gather(parameter, value, -dateTime) %>%
      filter(complete.cases(.))
    
    # da <- met %>%
    #   left_join(ra, 'dateTime') %>%
    #   left_join(camera$train_events, 'dateTime') %>%
    #   gather(parameter, value, -dateTime)
    
    return(list("da" = da,
                "train_images" = camera$train_images,
                "train_detects" = camera$train_detects))
  }
  
  return(data.frame())
}

# Function to gather/process logs, then upload
report_daily <- function(day) {
  
  # Collect and process log files for the day
  total <- get_logs(day = day)
  
  if (nrow(total$da) > 0) {
    
    # fname <- paste0('daily_', format(day), '.csv')
    # fpath <- paste0(out.dir, 'logs/', fname)
    # write.csv(total$da, fpath, row.names = F)
    save_da(total, day)

  }
}


# run_service()
report_daily(Sys.Date()-1)

# Script to gather log data and push to AWS server

require(tidyverse)
require(DBI)
require(RMariaDB)
require(httr)

source('config/reporting_config.R')



save_df <- function(df, name, day) {
  
  fname <- paste0(name, '/', format(day), '.csv')
  
  fpath <- paste0(dir_logs, fname)
  
  write.csv(df, fpath, row.names = F)
  
  return(list(fpath = fpath, fname = fname))
}


post_df <- function(df, fpath, fname, type) {
  
  # first create a tar ball of the file
  system(paste0('tar -cvzf ',fpath,'.tgz',' ',fpath))
  
  body = list(type = type,
              file = upload_file(paste0(fpath,'.tgz')),
              device_id = device_id,
              filename = fname,
              tablename = type)
  
  r <- POST(post_url, body = body, encode = "multipart")
  # print(content(r,"text"))
  
}


post_image <- function(filename) {
  
  body = list(type = "image",
              file = upload_file(paste0(dir_images, filename)),
              device_id = device_id,
              filename = filename)
  
  r <- POST(post_url, body=body, encode="multipart")
  # print(content(r,"text"))
}


save_da <- function(da, day) {
  
	# 1. save each dataframe in a csv file
	# 2. upload/post each csv file to cloud
	# 3. upload/post each image from train_images to cloud

  # print(nrow(da$da))
	da_file <- save_df(da$da, "daily_aggregate", day = day)
	
	post_df(da$da, da_file$fpath, da_file$fname, "daily_aggregate_v3")
	
	if (nrow(da$train_images) > 0) {
	  
	  train_images_file <- save_df(da$train_images, "train_images", day = day)
	  
	  post_df(da$train_images,
	          train_images_file$fpath,
	          train_images_file$fname, "train_images")
	  
	  sapply(da$train_images$filename, post_image)
	}
	
	if (nrow(da$train_detect) > 0) {
	  
	  train_detects_file <- save_df(da$train_detect, "train_detects", day = day)
	  
	  post_df(da$train_detect, train_detects_file$fpath,
	          train_detects_file$fname, "train_detects")
	
	}
	
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
  # returns dataframe with the following headers (9) - 
  # dateTime,outTemp,outHumidity,rain,windSpeed,windDir,windGust,windGustDir,inTemp

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
  #      headers(4) - dateTime, event_id, is_stat, is_moving
  #     
	# 2. train_detetcs - exact copy of the sql table `train_detects`
  #     headers(10) - id, event_id, type, image_id, label, score, x0, y0, x1, y1
	# 3. train_images - exact copy of the sql table `train_images`
  #     headers(3) -  id, filename, event_id

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
    # table `train_events` has columns - id, start, end

  	res <- dbSendQuery(train_db_con, query)
    # following line mutates train_events to have fields - dateTime, event_id 
  	train_events <- dbFetch(res)
    dbClearResult(res)
    if(nrow(train_events) == 0){
      train_events <- data.frame(rbind(c(-1, startTime, endTime))) # empty frame
    }
    train_events <- train_events %>%
                    pmap_df(~data.frame(dateTime=seq(..2,..3), event_id=..1)) %>%
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
    dbClearResult(res)
  	train_detect_for_events <- select(train_detects, event_id, type)

  	# add `is_stat` to train_events
  	train_events <- train_events %>%
  					left_join(subset(train_detect_for_events, type == 2), 'event_id') %>%
  					mutate(type = ifelse(is.na(type), -1, type)) %>%
  					mutate(is_stat = ifelse(type == 2, 1, 0)) %>% # here 1=TRUE, 0=FALSE
  					select(-type)

  	# add `is_moving` to train events
  	train_events <- train_events %>%
  					left_join(subset(train_detect_for_events, type == 1), 'event_id') %>%
  					mutate(type = ifelse(is.na(type), -1, type)) %>%
  					mutate(is_moving = ifelse(type == 1, 1, 0)) %>% # here 1=TRUE, 0=FALSE
  					select(-type)

  	train_events <- train_events[!duplicated(train_events$dateTime), ]

  	# query <- query <- paste("SELECT *
  	# 		FROM train_images
  	# 		WHERE event_id >= ", start_event_id, 
  	# 		"AND event_id <= ", end_event_id, ";")

    query <- paste("SELECT *
        FROM train_images
        WHERE dateTime >= ", startTime, 
        "AND dateTime <= ", endTime, ";")

  	res <- dbSendQuery(train_db_con, query)
  	train_images <- dbFetch(res)
    dbClearResult(res)

  	rvalue <- list("train_events" = train_events, "train_detects" = train_detects,
  	               "train_images" = train_images)

  	return(rvalue)
}

get_pa <- function(day) {

  # returns 1 dataframe
  #  headers(10) - dateTime, pm1, pm2.5, pm10, p0.3, p0.5, p1, p2.5, p5, p10

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

get_ra <- function(day) {
  
  # returns 1 dataframe
  # headers(22) - dateTime, p03_a[b,c], p05_a[b,c], p10_a[b,c], p25_a[b,c], p50_a[b,c], p100_a[b,c], pm25_a[b,c]
  
  startTime <- as.POSIXct(paste(format(day), '00:00:00'),
                          format = '%Y-%m-%d %H:%M:%S')
  endTime <- as.POSIXct(paste(format(day), '23:59:59'),
                        format = '%Y-%m-%d %H:%M:%S')
  startTime <- as.numeric(startTime)
  endTime <- as.numeric(endTime)
  
  ra_db_con <- dbConnect(RMariaDB::MariaDB(),
                         user = mysql_user,
                         password = mysql_pw,
                         dbname = mysql_db_trainspotting,
                         host= mysql_host)
  query <- paste("SELECT *
          FROM rugged_air 
          WHERE dateTime >=", startTime, 
                 "AND dateTime < ", endTime, 
                 "ORDER BY dateTime ;")
  
  res <- dbSendQuery(ra_db_con, query)
  ra <- dbFetch(res) 
  
  dbClearResult(res)
  dbDisconnect(ra_db_con)
  return(ra)
}

get_logs <- function(day) {
  
  # returns 3 dataframes - 
  # 1. da (daily_aggregate)
  #  headers(21) - 
  #   from met - dateTime, outTemp, outHumidity, rain, windSpeed,
  #              windDir, windGust, windGustDir, inTemp
  #   from camera - event_id, is_stat, is_moving
  #   from pa - pm1, pm2.5, pm10, p0.3, p0.5, p1, p2.5, p5, p10

  # 2. train_detetcs - exact copy of the sql table `train_detects`
  #     headers(10) - id, event_id, type, image_id, label, score, x0, y0, x1, y1

  # 3. train_images - exact copy of the sql table `train_images`
  #     headers(3) -  id, filename, event_id

  # Collect and process log files
  met <- get_met(day = day)
  camera <- get_camera(day = day)
  ra <- get_ra(day = day)
  
  if (!is.null(met) & !is.null(camera) & !is.null(ra)) {
    
    # Combine into final dataset. Start with a 1 second data frame
    da <- data.frame(
      dateTime = seq.POSIXt(as.POSIXct(paste(day, '00:00:00')),
                            as.POSIXct(paste(day, '23:59:59')),
                            1)) %>%
      mutate(dateTime = as.numeric(dateTime)) %>%
      left_join(met, 'dateTime') %>%
      left_join(ra, 'dateTime') %>%
      left_join(camera$train_events, 'dateTime') %>%
      gather(parameter, value, -dateTime) %>%
      filter(complete.cases(.))
    
    # da <- met %>%
    #   left_join(ra, 'dateTime') %>%
    #   left_join(camera$train_events, 'dateTime') %>%
    #   gather(parameter, value, -dateTime)
    
    return(list("da" = da,
                "train_images" = camera$train_images,
                "train_detects" = camera$train_detects))
  }
  
  return(data.frame())
}

# Function to gather/process logs, then upload
report_daily <- function(day) {
  
  # Collect and process log files for the day
  total <- get_logs(day = day)
  
  if (nrow(total$da) > 0) {
    
    # fname <- paste0('daily_', format(day), '.csv')
    # fpath <- paste0(out.dir, 'logs/', fname)
    # write.csv(total$da, fpath, row.names = F)
    save_da(total, day)

  }
}


# run_service()
report_daily(Sys.Date()-1)
