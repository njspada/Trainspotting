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
	$query = "select * from device_stats where device_id=$id order by dateTime desc limit 1;";
	list($result,$mysqli) = run_query($query);
	$row = $result->fetch_assoc();
	if($row){
		array_push($device_stats, array_merge($device,$row));
	}
}

$cols = ['id','url','report_time','mysql','run_ngrok','run_camera','run_purple_air','run_weewx'];
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
		$table->td($device_id,$col,$stat[$col]);
	}
}

$table->addRowStriping();
$html = $table->render();
echo $html;



// $table = \Donquixote\Cellbrush\Table\Table::create()
// 	->addRowName('rhead')
// 	->addColNames(['id','url','report_time','mysql','run_ngrok','run_camera','run_purple_air','run_weewx'])
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// 	->th('rhead','id','id')
// foreach($devices as $device){

// }


// $table = \Donquixote\Cellbrush\Table\Table::create()
//   ->addRowNames(['row0', 'row1', 'row2'])
//   ->addColNames(['col0', 'col1', 'col2'])
//   ->td('row0', 'col0', 'Diag 0')
//   ->td('row1', 'col1', 'Diag 1')
//   ->td('row2', 'col2', 'Diag 2')
// ;
// $html = $table->render();
// echo $html;

?>