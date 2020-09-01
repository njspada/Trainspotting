<?php

function run_query($query){
	$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
    if($mysqli->connect_errno) {
        echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
    }
    return array($mysqli->query($query),$mysqli);

    // if($mysqli->query($query) === TRUE){
    //     $site_id = $mysqli->insert_id;
    //     echo "site_id=$site_id;";
    // }
    // else{
    //     echo "there was an error\n";
    //     echo $mysqli->error;
    // }
}

function get(&$var, $default=null) {
    return isset($var) ? $var : $default;
}

?>