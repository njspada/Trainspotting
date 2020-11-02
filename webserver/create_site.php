<?php

include 'run_query.php';

if(isset($_GET['site_code'])){
    $code = $_GET['site_code'];
	$name = get($_GET['site_name'], 'name');
    $notes = get($_GET['site_notes'], 'notes');
    $latitude = get($_GET['latitude'], 0.00);
    $longitude = get($_GET['longitude'], 0.00);

	$query = "INSERT INTO sites (site_code,site_name,site_notes,latitude,longitude) VALUES ('$code','$name','$notes',$latitude,$longitude);";
	// $mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");

    // if($mysqli->connect_errno) {
    //     echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
    // }

    list($result,$mysqli) = run_query($query);
    if($result === TRUE){
        $site_id = $mysqli->insert_id;
        echo "site_id=$site_id;";
    }
    else{
        echo "there was an error\n";
        echo $mysqli->error;
    }
}


?>