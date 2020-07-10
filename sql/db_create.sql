CREATE DATABASE IF NOT EXISTS `trainspotting` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `trainspotting`;

-- --------------------------------------------------------

--
-- Table structure for table `purple_air`
--

CREATE TABLE `purple_air` (
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

CREATE TABLE `camera_detects` (
  `timestamp` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `conf` float NOT NULL,
  `label` varchar(25) NOT NULL,
  `x0` int(11) NOT NULL,
  `y0` int(11) NOT NULL,
  `x1` int(11) NOT NULL,
  `y1` int(11) NOT NULL,
  `filename` varchar(35) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Store output from run_camera.py';

CREATE TABLE `trainspotting`.`train_events` ( `id` INT NOT NULL AUTO_INCREMENT COMMENT 'event id auto increment' , `start` TIMESTAMP NOT NULL COMMENT 'even start imestamp' , `end` TIMESTAMP NOT NULL COMMENT 'event end timestamp' , PRIMARY KEY (`id`)) ENGINE = InnoDB;
