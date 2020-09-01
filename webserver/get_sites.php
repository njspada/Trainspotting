<?php 

require __DIR__ . '/vendor/autoload.php';
include 'run_query.php';

$print_attached = get($_GET['attached'],'no');
$query = "SELECT * FROM sites;";
list($result,$mysqli) = run_query($query);
$result = $result->fetch_all(MYSQLI_ASSOC);
$rows=array();
foreach($result as $site){
	$row = array('device_id'=>-1,'start'=>-1,'end'=>-1);
	if($print_attached == 'no'){
		$rows[]= array_merge($row,$site);
	}
	else{
		$query = "SELECT * FROM site_usage WHERE site_id=$site[site_id] AND end=0;";
		list($records,$mysqli2) = run_query($query);
		while($row = $records->fetch_assoc()){
			$row['start'] = date('r', $row['start']);
			$rows[]= array_merge($row,$site);
		}
	}
}

$cols = ['site_id','site_code','site_name','site_notes','latitude','longitude','device_id','start','end'];
$table = \Donquixote\Cellbrush\Table\Table::create()
	->addRowName('rhead')
	->addColNames($cols);
foreach($cols as $col){
	$table->th('rhead',$col,$col);
}
foreach($rows as $index=>$row){
	$table->addRowName($index);
	foreach($cols as $col){
		$table->td($index,$col,$row[$col]);
	}
}

$table->addRowStriping();
$html = $table->render();
$style = "<head><style>table,td,th {border:1px black solid; test-align:left;}</style></head>";
echo $style;
echo $html;

?>