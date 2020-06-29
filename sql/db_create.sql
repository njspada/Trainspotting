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
