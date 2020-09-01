<?php

	include 'run_query.php';
	$device_id = get($_GET['device_id'], -1);
	$site_id = get($_GET['site_id'], -1);
	$site_code = get($_GET['site_code'], -1);

	if($device_id==-1){
		exit("please provide device_id");
	}

	if($site_id == -1){ // lookup site site_id suing site id
		if($site_code==-1){
			exit("please provide site id or code");
		}
		$query = "SELECT site_id FROM sites WHERE site_code=$site_code;";
		list($result,$mysqli) = run_query($query);
		if($result = $result->fetch_assoc()){
			$site_id = $result['site_id'];
		}
		else{
			exit("site_code does not exist. exiting.");
		}
	}
	$end = time();
	$query = "UPDATE site_usage SET end=$end WHERE device_id=$device_id AND end=0 AND site_id=$site_id;";
	list($result,$mysqli) = run_query($query);
	echo $mysqli->error;

?>