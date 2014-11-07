<?php

function recurse_copy($src,$dst) { 
	if(is_link($src)) {
		return;
	}
    $dir = opendir($src); 
	if($dir === false) {
		throw new Exception("Could not open directory: ".$src);
	}
    @mkdir($dst); 
    while(false !== ( $file = readdir($dir)) ) { 
        if (( $file != '.' ) && ( $file != '..' )) { 
            if ( is_dir($src . '/' . $file) ) { 
                recurse_copy($src . '/' . $file,$dst . '/' . $file); 
            } 
            else { 
				try {
					if(!is_link($src)) {
						copy($src . '/' . $file,$dst . '/' . $file);
					}
				}
				catch(Exception $e) {
					throw new Exception("Could not copy files: ".$src . "/" . $file. " to: ". $dst . "/" . $file); 
				}
            } 
        } 
    } 
    closedir($dir); 
} 

function rrmdir($dir) { 
   if (is_dir($dir)) { 
     $objects = scandir($dir); 
     foreach ($objects as $object) { 
       if ($object != "." && $object != "..") { 
         if (filetype($dir."/".$object) == "dir") {
			chmod($dir."/".$object, 0777);
			rrmdir($dir."/".$object);
		}
		else {
			chmod($dir."/".$object, 0777);
			unlink($dir."/".$object); 
		}
       } 
     } 
     reset($objects); 
     rmdir($dir); 
   } 
} 

try {
	if($argc != 4) {
		exit("Incorrect number of arguments. Expecting 3 but got " . ($argc - 1) . ". Exiting.");
	}
	else {
		$drupal = $argv[1];
		$source = $argv[2];
		$dest = $argv[3];

		echo $argv[1] . "\n";
		echo $argv[2] . "\n";
		echo $argv[3] . "\n\n";
		
		if(is_dir($dest)) {
			echo "Directory already exists. Deleting directory before copying new files... ";
			rrmdir($dest);
			echo "completed.\n";
		}
		mkdir($dest);
		echo "Creating directory... completed.\n";

		if(is_link($source . "\\includes")) {
			echo "Site uses Drupal. Copying Drupal files first... ";
			recurse_copy($drupal, $dest);
			echo "completed.\n";
			echo "Copying source to directory... ";
			recurse_copy($source . "\\sites", $dest . "\\sites");
		}
		else {
			echo "Copying source to directory... ";
			recurse_copy($source, $dest);
		}

		echo "completed.\n";

		echo "Renaming source folder...";
		$parentfolder = dirname($dest);
		$dirs = explode("\\",str_replace("/","\\",$dest));
		$curdir = array_pop($dirs);
		$curdir = preg_replace("/\.colorado\.edu/i","",$curdir);
		$dirs[] = $curdir;
		rename($dest,implode("\\",$dirs));
		echo "done";
	}
}
catch(Exception $e) {
	var_dump($e->getMessage());
	die();
}