-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Jul 09, 2020 at 05:56 PM
-- Server version: 5.7.30-0ubuntu0.18.04.1
-- PHP Version: 7.2.24-0ubuntu0.18.04.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `trainspotting`
--
CREATE DATABASE IF NOT EXISTS `trainspotting` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `trainspotting`;

-- --------------------------------------------------------

--
-- Table structure for table `camera_detects`
--

DROP TABLE IF EXISTS `camera_detects`;
CREATE TABLE IF NOT EXISTS `camera_detects` (
  `timestamp` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `conf` float NOT NULL,
  `label` varchar(25) NOT NULL,
  `x0` int(11) NOT NULL,
  `y0` int(11) NOT NULL,
  `x1` int(11) NOT NULL,
  `y1` int(11) NOT NULL,
  `filename` varchar(35) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Store output from run_camera.py';

-- --------------------------------------------------------

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
CREATE TABLE IF NOT EXISTS `images` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'detect id auto increment',
  `event_id` int(11) NOT NULL,
  `filename` varchar(35) NOT NULL,
  `box` varchar(35) NOT NULL,
  `labels` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `event_id` (`event_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `purple_air`
--

DROP TABLE IF EXISTS `purple_air`;
CREATE TABLE IF NOT EXISTS `purple_air` (
  `datetime` datetime NOT NULL,
  `pm2.5` float NOT NULL,
  `pm1` float NOT NULL,
  `pm10` float NOT NULL,
  `p0.3` float NOT NULL,
  `p0.5` float NOT NULL,
  `p1` float NOT NULL,
  `p2.5` float NOT NULL,
  `p5` float NOT NULL,
  `p10` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Purple Air Data';

-- --------------------------------------------------------

--
-- Table structure for table `train_events`
--

DROP TABLE IF EXISTS `train_events`;
CREATE TABLE IF NOT EXISTS `train_events` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'event id auto increment',
  `start` timestamp NULL DEFAULT NULL COMMENT 'even start imestamp',
  `end` timestamp NULL DEFAULT NULL COMMENT 'event end timestamp',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `images`
--
ALTER TABLE `images`
  ADD CONSTRAINT `images_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `train_events` (`id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
