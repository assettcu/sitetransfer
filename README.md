Site Transfer
============

Transfer website from one environment to another.

Currently working on these environment scenarios:

                TO
          Prod  Test  Dev
    Prod  [ ]   [x]   [ ]
    Test  [ ]   [ ]   [ ]
    Dev   [ ]   [ ]   [ ]

USAGE
python C:\Python34\assettdev.py {1} {2} {3}
  1. Name of website to copy. ie: phys for phys.colorado.edu or atoc for atoc.colorado.edu
  2. Assettdev MySQL database username 
  3. Assettdev MySQL database password

EXAMPLE
python C:\Python34\sitetransfer.py phys prod_to_test {password}
