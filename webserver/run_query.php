<?php
date_default_timezone_set('America/Los_Angeles');
function run_query($query){
	$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
    if($mysqli->connect_errno) {
        echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
    }
    return array($mysqli->query($query),$mysqli);
}

function get(&$var, $default=null) {
    return isset($var) ? $var : $default;
}

?>