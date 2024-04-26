<?php

$file = $_FILES['status']['tmp_name'];
// create sql query to insert file
$query = "LOAD DATA LOCAL INFILE '$file' ".
     "INTO TABLE status ".
     "FIELDS TERMINATED BY ',' ".
     "LINES TERMINATED BY '\n' ".
     "(dateTime,device_id,service,loadstate,activestate,substate) ;"; 

$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if($mysqli->connect_errno) {
    echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
}

if($mysqli->query($query) === TRUE){
    // echo "successfully inserted";
}
else{
    echo "there was an error\n";
    echo $mysqli->error;
}

$url = $_GET['url'];
$device_id = $_GET['device_id'];
$dateTime=$_GET['dateTime'];
$query = "UPDATE field_devices SET url='$url' WHERE id=$device_id;";
$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if($mysqli->connect_errno) {
    echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
}

if($mysqli->query($query) === TRUE){
    // echo "successfully inserted";
}
else{
    echo "there was an error with url\n";
    echo $mysqli->error;
}

?>