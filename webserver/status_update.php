<?php
include 'run_query.php';
// $run_weewx = get($_GET['run_weewx'],0);
// $run_ngrok = get($_GET['run_ngrok'],0);
// $run_camera = get($_GET['run_camera'],0);
// $run_purple_air = get($_GET['run_purple_air'],0);
// $mysql = get($_GET['mysql'],0);
$post = json_decode(file_get_contents('php://input'),true);
var_dump($post);
$url = get($post['url'],'0');
$device_id = $post['device_id'];
$dateTime=$post['dateTime'];

$processes = ['run_camera','run_ngrok','run_purple_air','mysql','run_weewx','nvargus_daemon'];
$fields = "(dateTime,device_id";
$values = "($dateTime,$device_id";

echo $dateTime;

foreach($processes as $p){
	$fields = $fields.",$p,$p"."_mem";
	$values = $values.',\''.get($post[$p],'0').'\',\''.get($post[$p.'_mem'],'0').'\'';
}

$fields = $fields.')';
$values = $values.')';

$query = "INSERT INTO new_device_stats $fields VALUES $values;";

// $query = "insert into device_stats (dateTime,run_weewx,run_camera,run_ngrok,run_purple_air,device_id,url,mysql) values ($dateTime,'$run_weewx','$run_camera','$run_ngrok','$run_purple_air',$device_id,'$url','$mysql');";
echo $query;
run_query($query);

?>