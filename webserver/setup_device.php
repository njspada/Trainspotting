<?php

if(isset($_GET['name']) and isset($_GET['report_time'])){
	$name = $_GET['name'];
    $report_time = $_GET['report_time'];
	$query = "INSERT INTO field_devices (name,report_time) VALUES ('$name','$report_time');";
	$mysqli = new mysqli("localhost", "johndoe", "password", "trainspotting");
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
