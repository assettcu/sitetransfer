<?php
$ch = curl_init();

curl_setopt_array($ch, array(
    CURLOPT_RETURNTRANSFER => 1,
    CURLOPT_URL => "http://assetttest.colorado.edu/drushrunner.php?site=" . $argv[1],
));
$output = curl_exec($ch);
curl_close($ch);
	var_dump($output);
if(!$output){
    die('Error: "' . curl_error($ch) . '" - Code: ' . curl_errno($ch));
}
else {
	var_dump($output);
}

?>