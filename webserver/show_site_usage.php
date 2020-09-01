<?php 

// This returns an associative array of device_id, device_name, and report_time

$query = "SELECT * FROM sites;";
$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if($mysqli->connect_errno) {
    echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
}

$result = $mysqli->query($query);
$result = $result->fetch_all(MYSQLI_ASSOC);
echo "site_id    site_code    site_name    site_notes    latitude    longitude\r\n";
foreach($result as $value){
	echo "$value[site_id]    $value[site_code]    $value[site_name]    $value[site_notes]    $value[latitude]    $value[longitude]\n";
}

?>