<?php
include 'run_query.php';
$run_weewx = get($_GET['run_weewx'],0);
$run_ngrok = get($_GET['run_ngrok'],0);
$run_camera = get($_GET['run_camera'],0);
$run_purple_air = get($_GET['run_purple_air'],0);
$mysql = get($_GET['mysql'],0);
$url = $_GET['url'];
$device_id = $_GET['device_id'];
$dateTime=$_GET['dateTime'];

$query = "insert into device_stats (dateTime,run_weewx,run_camera,run_ngrok,run_purple_air,device_id,url,mysql) values ($dateTime,'$run_weewx','$run_camera','$run_ngrok','$run_purple_air',$device_id,'$url','$mysql');";

run_query($query);

?>