<?php
require __DIR__ . '/vendor/autoload.php';
include 'run_query.php';
// // get url, report time, service stats
$query = "select * from field_devices;";
list($result,$mysqli) = run_query($query);
$devices = $result->fetch_all(MYSQLI_ASSOC);
$device_stats = array();

foreach($devices as $device){
	$id = $device['id'];
	//echo $id;
	$query = "select * from new_device_stats where device_id=$id order by dateTime desc limit 1;";
	list($result,$mysqli) = run_query($query);
	$row = $result->fetch_assoc();
	if($row){
		$row['dateTime'] = date('r', $row['dateTime']);
		array_push($device_stats, array_merge($device,$row));
	}
}

$cols = ['id','name','dateTime','url','report_time','mysql','run_ngrok','run_camera','run_purple_air','run_weewx','nvargus_daemon'];
$table = \Donquixote\Cellbrush\Table\Table::create()
	->addRowName('rhead')
	->addColNames($cols);
foreach($cols as $col){
	$table->th('rhead',$col,$col);
}
foreach($device_stats as $stat){
	$device_id = strval($stat['id']);
	$table->addRowName($device_id);
	foreach($cols as $col){
		$text = $stat[$col];
		if($mem=$stat[$col.'_mem']){
			$text = $text.'<br>'.$mem;
		}
		$table->td($device_id,$col,$text);
	}
}

$table->addRowStriping();
$html = $table->render();
$style = "<head><style>table,td,th {border:1px black solid; test-align:left;}</style></head>";
echo $style;
echo $html;

?>