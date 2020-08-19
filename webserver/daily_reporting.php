<?php

echo "hiiiiiiii!";
$output_dir = "/home/bitnami/output/";

if(isset($_POST["type"])) {
    if($_POST["type"] == "image"){
        // save_file($_FILES['file']['tmp_name'], "images/".$_POST['device_id'].$_POST['filename']);
        save_file($_FILES['file']['tmp_name'], $output_dir."images/".$_POST['filename']);
    }
    else{
        save_da();
    }
}


function save_file($source, $destination){
	echo "trying to save file";
	chmod($destination, 0777);
    move_uploaded_file($source, $destination);
}

function save_da(){
    $query = "";
    $filename = $_POST["filename"];
    // $device_id = $_POST["device_id"];
    $file = $_FILES['file']['tmp_name'];
    $tablename = $_POST["tablename"];
    // echo $tablename;
    $output_dir = "/home/bitnami/output/";
    // first save the file
    // save_file($file, "logs/".$device_id.$filename);
    save_file($file, $output_dir."logs/".$filename);

    // create field list from file header
    // $header = fgets(fopen($file,'r'));
    // $header_array = explode(",",$header);

    // $header_array[count($header_array)-1] = explode("\n",$header_array[count($header_array)-1])[0];
    // $header_array = array_map(function($s) {return '`'.(str_replace("\"", "", $s)).'`'; }, $header_array);
    // $header = implode(',',$header_array);

    // // create sql query to insert file
    // $query = "LOAD DATA LOCAL INFILE '$file' ".
    //      "INTO TABLE $tablename ".
    //      "FIELDS TERMINATED BY ',' ".
    //      "LINES TERMINATED BY '\n' ".
    //      "IGNORE 1 LINES ".
    //      "($header);"; 
    // echo $query;

    // $mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
    // if($mysqli->connect_errno) {
    //     echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
    // }

    // if($mysqli->query($query) === TRUE){
    //     echo "successfully inserted";
    // }
    // else{
    //     echo "there was an error\n";
    //     echo $mysqli->error;
    // }
}

?>
