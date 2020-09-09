-- MySQL dump 10.13  Distrib 8.0.20, for Linux (x86_64)
--
-- Host: localhost    Database: trainspotting
-- ------------------------------------------------------
-- Server version	8.0.20

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES UTF8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `daily_aggregate`
--

DROP TABLE IF EXISTS `daily_aggregate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_aggregate` (
  `device_id` int NOT NULL,
  `dateTime` int NOT NULL,
  `outTemp` float NOT NULL,
  `outHumidity` float NOT NULL,
  `rain` float NOT NULL,
  `windSpeed` float NOT NULL,
  `windDir` float NOT NULL,
  `windGust` float NOT NULL,
  `windGustDir` float NOT NULL,
  `inTemp` float NOT NULL,
  `pm2.5` float NOT NULL,
  `pm1` float NOT NULL,
  `pm10` float NOT NULL,
  `p0.3` float NOT NULL,
  `p0.5` float NOT NULL,
  `p1` float NOT NULL,
  `p2.5` float NOT NULL,
  `p5` float NOT NULL,
  `p10` float NOT NULL,
  `event_id` int NOT NULL,
  `is_moving` tinyint(1) NOT NULL,
  `is_stat` tinyint(1) NOT NULL,
  PRIMARY KEY (`device_id`,`dateTime`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Daily aggregated seconds data';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `device_stats`
--

DROP TABLE IF EXISTS `device_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `device_stats` (
  `dateTime` int NOT NULL,
  `run_weewx` varchar(20) NOT NULL,
  `run_camera` varchar(20) NOT NULL,
  `run_ngrok` varchar(20) NOT NULL,
  `run_purple_air` varchar(20) NOT NULL,
  `device_id` int NOT NULL,
  `url` varchar(40) NOT NULL,
  `mysql` varchar(40) NOT NULL,
  KEY `device_id` (`device_id`,`dateTime`),
  CONSTRAINT `device_stats_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `field_devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `device_url`
--

DROP TABLE IF EXISTS `device_url`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `device_url` (
  `dateTime` int NOT NULL,
  `device_id` int NOT NULL,
  `url` varchar(40) NOT NULL,
  KEY `device_id` (`device_id`),
  CONSTRAINT `device_url_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `field_devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `field_devices`
--

DROP TABLE IF EXISTS `field_devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `field_devices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `notes` varchar(100) NOT NULL DEFAULT '----',
  `name` varchar(25) NOT NULL,
  `report_time` varchar(5) NOT NULL DEFAULT '55 23',
  `url` varchar(40) NOT NULL DEFAULT 'none',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=latin1 COMMENT='List of devices in the field';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `site_usage`
--

DROP TABLE IF EXISTS `site_usage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `site_usage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `device_id` int NOT NULL,
  `site_id` int NOT NULL,
  `start` int NOT NULL,
  `end` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `site_id` (`site_id`),
  CONSTRAINT `site_usage_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `field_devices` (`id`) ON DELETE CASCADE,
  CONSTRAINT `site_usage_ibfk_2` FOREIGN KEY (`site_id`) REFERENCES `sites` (`site_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sites`
--

DROP TABLE IF EXISTS `sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sites` (
  `site_id` int NOT NULL AUTO_INCREMENT,
  `site_code` varchar(25) NOT NULL,
  `site_name` varchar(25) NOT NULL DEFAULT 'name',
  `site_notes` varchar(400) NOT NULL DEFAULT 'notes',
  `latitude` float NOT NULL DEFAULT '0',
  `longitude` float NOT NULL DEFAULT '0',
  PRIMARY KEY (`site_id`),
  UNIQUE KEY `site_code` (`site_code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status`
--

DROP TABLE IF EXISTS `status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `status` (
  `dateTime` int NOT NULL,
  `device_id` int NOT NULL,
  `service` varchar(25) NOT NULL,
  `loadstate` varchar(25) NOT NULL,
  `activestate` varchar(25) NOT NULL,
  `substate` varchar(25) NOT NULL,
  KEY `dateTime` (`dateTime`,`device_id`,`service`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `train_detects`
--

DROP TABLE IF EXISTS `train_detects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `train_detects` (
  `device_id` int NOT NULL,
  `id` int NOT NULL,
  `event_id` int NOT NULL,
  `type` int NOT NULL,
  `image_id` int NOT NULL,
  `label` varchar(25) NOT NULL,
  `score` float NOT NULL,
  `x0` float NOT NULL,
  `y0` float NOT NULL,
  `x1` float NOT NULL,
  `y1` float NOT NULL,
  PRIMARY KEY (`device_id`,`id`),
  KEY `train_detects_ibfk_1` (`type`),
  CONSTRAINT `train_detects_ibfk_1` FOREIGN KEY (`type`) REFERENCES `train_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Bounding box coords are relative. ';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `train_images`
--

DROP TABLE IF EXISTS `train_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `train_images` (
  `device_id` int NOT NULL,
  `id` int NOT NULL,
  `filename` varchar(100) NOT NULL,
  `event_id` int NOT NULL,
  PRIMARY KEY (`device_id`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='filenames are actually full paths.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `train_types`
--

DROP TABLE IF EXISTS `train_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `train_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-09-02 21:12:39
