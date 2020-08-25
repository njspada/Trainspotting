-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 19, 2020 at 02:15 PM
-- Server version: 5.7.31-0ubuntu0.18.04.1
-- PHP Version: 7.2.24-0ubuntu0.18.04.6

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `trainspotting`
--
DROP DATABASE IF EXISTS `trainspotting`;
CREATE DATABASE IF NOT EXISTS `trainspotting` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `trainspotting`;

-- --------------------------------------------------------

--
-- Table structure for table `daily_aggregate`
--

DROP TABLE IF EXISTS `daily_aggregate`;
CREATE TABLE `daily_aggregate` (
  `dateTime` int(11) NOT NULL,
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
  `event_id` int(11) NOT NULL,
  `is_moving` tinyint(1) NOT NULL,
  `is_stat` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Daily aggregated seconds data';

-- --------------------------------------------------------

--
-- Table structure for table `field_devices`
--

DROP TABLE IF EXISTS `field_devices`;
CREATE TABLE `field_devices` (
  `id` int(11) NOT NULL,
  `latitude` float NOT NULL DEFAULT '0',
  `longitude` float NOT NULL DEFAULT '0',
  `notes` varchar(100) NOT NULL DEFAULT '----',
  `name` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='List of devices in the field';

-- --------------------------------------------------------

--
-- Table structure for table `train_detects`
--

DROP TABLE IF EXISTS `train_detects`;
CREATE TABLE `train_detects` (
  `id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `type` int(11) NOT NULL,
  `image_id` int(11) NOT NULL,
  `label` varchar(25) NOT NULL,
  `score` float NOT NULL,
  `x0` float NOT NULL,
  `y0` float NOT NULL,
  `x1` float NOT NULL,
  `y1` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Bounding box coords are relative. ';

-- --------------------------------------------------------

--
-- Table structure for table `train_images`
--

DROP TABLE IF EXISTS `train_images`;
CREATE TABLE `train_images` (
  `id` int(11) NOT NULL,
  `filename` varchar(100) NOT NULL,
  `event_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='filenames are actually full paths.';

-- --------------------------------------------------------

--
-- Table structure for table `train_types`
--

DROP TABLE IF EXISTS `train_types`;
CREATE TABLE `train_types` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `daily_aggregate`
--
ALTER TABLE `daily_aggregate`
  ADD KEY `da_index` (`dateTime`);

--
-- Indexes for table `field_devices`
--
ALTER TABLE `field_devices`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `train_detects`
--
ALTER TABLE `train_detects`
  ADD KEY `type` (`type`),
  ADD KEY `td_index` (`id`);

--
-- Indexes for table `train_images`
--
ALTER TABLE `train_images`
  ADD KEY `ti_index` (`id`);

--
-- Indexes for table `train_types`
--
ALTER TABLE `train_types`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `field_devices`
--
ALTER TABLE `field_devices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `train_types`
--
ALTER TABLE `train_types`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- Constraints for dumped tables
--

--
-- Constraints for table `train_detects`
--
ALTER TABLE `train_detects`
  ADD CONSTRAINT `train_detects_ibfk_1` FOREIGN KEY (`type`) REFERENCES `train_types` (`id`);
SET FOREIGN_KEY_CHECKS=1;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
