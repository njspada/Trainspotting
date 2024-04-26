<?php
//$root = __DIR__;
$root = "/home/bitnami/output/images";

function is_in_dir($file, $directory, $recursive = true, $limit = 1000) {
    //$directory = realpath($directory);
    //$parent = realpath($file);
    $parent = $root."/".$file;
    $i = 0;
    while ($parent) {
        if ($directory == $parent) return true;
        if ($parent == dirname($parent) || !$recursive) break;
        $parent = dirname($parent);
    }
    return false;
}

$path = null;
if (isset($_GET['file'])) {
    $path = $_GET['file'];
    $path = '/'.$path;
    // if (!is_in_dir($_GET['file'], $root)) {
    //     //echo "nulling";
    //     $path = null;
    // } else {
    //     $path = '/'.$path;
    // }
}

if (is_file($root.$path)) {
    $type = 'image/jpeg';
    header('Content-Type:'.$type);
    readfile($root.$path);
    return;
}

if ($path) echo '<a href="?file='.urlencode(substr(dirname($root.$path), strlen($root) + 1)).'">..</a><br />';
foreach (glob($root.$path.'/*') as $file) {
    //$file = realpath($file);
    $link = substr($file, strlen($root) + 1);
    echo '<a href="?file='.urlencode($link).'">'.basename($file).'</a><br />';
}
?>