<?php

$images_dir = "/home/bitnami/output/images/";
$filename = $_GET['filename'];
header('Content-Type: image/jpeg');
header('Content-Length: ' . filesize($images_dir.$filename));
echo file_get_contents($images_dir.$filename);

?>