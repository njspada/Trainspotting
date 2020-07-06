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

CREATE TABLE `trainspotting`.`camera_detects` ( `timestamp` TIMESTAMP NOT NULL , `conf` FLOAT NOT NULL , `label` VARCHAR(25) NOT NULL , `x0` INT NOT NULL , `y0` INT NOT NULL , `x1` INT NOT NULL , `y1` INT NOT NULL , `filename` INT NOT NULL ) ENGINE = InnoDB COMMENT = 'Store output from run_camera.py';


