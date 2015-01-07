<?php
if($argc != 3) {
	echo "\nIncorrect number of parameters.\n";
	exit;
}

$ch = curl_init("http://assettdev.colorado.edu/open/sitetransfer/wp.change-permalink.php?site=".$argv[1]."&permalink=".$argv[2]);
$output = curl_exec($ch);
curl_close($ch);
?>