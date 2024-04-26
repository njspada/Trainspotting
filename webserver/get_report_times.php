<?php 

// This returns an associative array of device_id, device_name, and report_time

$query = "SELECT id,name,report_time FROM field_devices;";
$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if($mysqli->connect_errno) {
    echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
}

$result = $mysqli->query($query);
$result = $result->fetch_all(MYSQLI_ASSOC);
echo "rtime    id    name\r\n";
foreach($result as $value){
	echo "$value[report_time]    $value[id]    $value[name]\n";
}

// if($mysqli->query($query) === TRUE){
//     $device_id = $mysqli->insert_id;
//     echo "$";
// }
// else{
//     echo "there was an error\n";
//     echo $mysqli->error;
// }

?>