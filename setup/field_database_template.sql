-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Aug 24, 2020 at 03:52 PM
-- Server version: 5.7.31-0ubuntu0.18.04.1
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
-- Table structure for table `purple_air`
--

CREATE TABLE `purple_air` (
  `dateTime` int(11) NOT NULL,
  `p03_avg` float NOT NULL,
  `p03_sd` float NOT NULL,
  `p10_avg` float NOT NULL,
  `p10_sd` float NOT NULL,
  `p25_avg` float NOT NULL,
  `p25_sd` float NOT NULL,
  `p50_avg` float NOT NULL,
  `p50_sd` float NOT NULL,
  `p100_avg` float NOT NULL,
  `p100_sd` float NOT NULL,
  `pm25_avg` float NOT NULL,
  `pm25_sd` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='One channel data from purple air';

-- --------------------------------------------------------

--
-- Table structure for table `train_detects`
--

CREATE TABLE `train_detects` (
  `id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `type` int(11) NOT NULL,
  `image_id` int(11) NOT NULL,
  `label` varchar(25) NOT NULL,
  `score` int(11) NOT NULL,
  `x0` int(11) NOT NULL,
  `y0` int(11) NOT NULL,
  `x1` int(11) NOT NULL,
  `y1` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `train_events`
--

CREATE TABLE `train_events` (
  `id` int(11) UNSIGNED NOT NULL COMMENT 'event id auto increment',
  `start` int(11) NOT NULL,
  `end` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `train_images`
--

CREATE TABLE `train_images` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(100) NOT NULL,
  `dateTime` int(11) NOT NULL,
  PRIMARY KEY(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `train_types`
--

CREATE TABLE `train_types` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `purple_air`
--
ALTER TABLE `purple_air`
  ADD PRIMARY KEY (`dateTime`),
  ADD KEY `dateTime` (`dateTime`);

--
-- Indexes for table `train_detects`
--
ALTER TABLE `train_detects`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `train_events`
--
ALTER TABLE `train_events`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `train_images`
--
ALTER TABLE `train_images`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `train_types`
--
ALTER TABLE `train_types`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `train_detects`
--
ALTER TABLE `train_detects`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3215;
--
-- AUTO_INCREMENT for table `train_events`
--
ALTER TABLE `train_events`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'event id auto increment', AUTO_INCREMENT=753;
--
-- AUTO_INCREMENT for table `train_images`
--
ALTER TABLE `train_images`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6330;
--
-- AUTO_INCREMENT for table `train_types`
--
ALTER TABLE `train_types`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
--
--
--
INSERT INTO train_types VALUES(1,"moving");
INSERT INTO train_types VALUES(2,"stationary");
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
