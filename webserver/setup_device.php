<?php

if(isset($_GET['name'])){
	$name = $_GET['name'];
	$query = "INSERT INTO field_devices (name) VALUES ('$name');";
	$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
    if($mysqli->connect_errno) {
        echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
    }

    if($mysqli->query($query) === TRUE){
        $device_id = $mysqli->insert_id;
        echo "device_id=$device_id;";
    }
    else{
        echo "there was an error\n";
        echo $mysqli->error;
    }
}


?>