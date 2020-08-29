<?php

// $output_dir = "/home/bitnami/output/";

// function save_file($source, $destination){
// 	// first create the right directory
// 	// then set 777 permissions for that directory
// 	// then move the file
// 	mkdir(pathinfo($destination)['dirname'], 0777, true);
//     move_uploaded_file($source, $destination);
// }

//save_file($_FILES['status']['tmp_name'], $output_dir."status/sta.txt");
$file = $_FILES['status']['tmp_name'];
// create sql query to insert file
$query = "LOAD DATA LOCAL INFILE '$file' ".
     "INTO TABLE status ".
     "FIELDS TERMINATED BY ',' ".
     "LINES TERMINATED BY '\n' ".
     "(dateTime,device_id,service,loadstate,activestate,substate) ;"; 

$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if($mysqli->connect_errno) {
    echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
}

if($mysqli->query($query) === TRUE){
    // echo "successfully inserted";
}
else{
    echo "there was an error\n";
    echo $mysqli->error;
}

?>