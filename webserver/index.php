<?php

// $uploaddir = "/";
// $uploadfile = $uploaddir . basename( $_FILES['file']['name']);

// if ($_FILES['file']['error'] == UPLOAD_ERR_OK               //checks for errors
//               && is_uploaded_file($_FILES['file']['tmp_name'])) { //checks that file is uploaded
//                 echo file_get_contents($_FILES['file']['tmp_name']); 
// }

//$file = file('test_da.csv');
$file = $_FILES['file']['tmp_name'];
$mysqli = new mysqli("localhost", "dhawal", "april+1Hitmonlee", "trainspotting");
if ($mysqli->connect_errno) {
     echo "Failed to connect to MySQL: (" . $mysqli->connect_errno . ") " . $mysqli->connect_error;
     }
     echo $mysqli->host_info . "\n";
$query = <<<eof
    LOAD DATA LOCAL INFILE '$file'
     INTO TABLE test_da
     FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
     LINES TERMINATED BY '\n'
    (f0,f1,f2,f3)
eof;

if($mysqli->query($query) === TRUE){
        echo "successfully inserted";
}
else{
        echo "there was an error\n";
        echo $mysqli->error;
}

?>
