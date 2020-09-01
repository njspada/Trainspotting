<?php 


function get(&$var, $default=null) {
    return isset($var) ? $var : $default;
}

$query = "SELECT * FROM sites;";
$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if($mysqli->connect_errno) {
    echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
}

$result = $mysqli->query($query);
$result = $result->fetch_all(MYSQLI_ASSOC);
echo "site_id    site_code    site_name    site_notes    latitude    longitude    device_id    start\r\n<br>";
foreach($result as $value){
	$device_id=-1;
	$start=-1;
	$end=-1;
	$query = "SELECT * FROM site_usage WHERE site_id=$value[site_id] AND end=0;";
	$r = $mysqli->query($query);
	if($r = $r->fetch_assoc()){
		$device_id = $r['device_id'];
		$start = $r['start'];
	}
	echo "$value[site_id]    $value[site_code]    $value[site_name]    $value[site_notes]    $value[latitude]    $value[longitude]    $device_id    $start    $end\n<br>";
}

?>