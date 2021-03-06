# assettdev.py
# by: Derek Baumgartner
# last modified: 10/31/2014
# python verison: 3
# description: Transfer production website to development server
#
#   OBJECTIVES
#   1. Copy files from production to assetttest.
#   2. Copy the database from production to assetttest.
#   3. Create a user in the database with proper permissions.
#   4. Update the site database so that links to productionsite.colorado.edu 
#   are replaced with assetttest.colorado.edu/productionsite.
#
#   USAGE
#   python C:\Python34\assettdev.py {1} {2} {3}
#       1. Name of website to copy. ie: phys for phys.colorado.edu or atoc for atoc.colorado.edu
#       2. Assettdev MySQL database username 
#       3. Assettdev MySQL database password (put in quotes is there are spaces)
#
#   EXAMPLE
#   C:\Python34\python C:\Python34\sitetransfer\sitetransfer.py phys username "multi word password"
#
#   

import os
import shutil
import sys
import glob
import subprocess
import time

# Global Vars
USER_PRIVS      = "SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES"
PRODUCTION_DIR  = os.path.normpath("//olympic.colorado.edu/web$/")
DEVELOPMENT_DIR = os.path.normpath("//assettdev.colorado.edu/web$/assetttest.colorado.edu")
PROTEUS_DIR     = os.path.normpath("//assettdev.colorado.edu/c$/proteus/")
PROTEUS_PHP     = os.path.normpath("//assettdev.colorado.edu/c$/proteus/proteus.php")
DB_BACKUP_DIR   = os.path.normpath("//olympic.colorado.edu/c$/db backup/")
MIRRORDIR_PATH  = os.path.normpath("//olympic.colorado.edu/c$/Python34/sitetransfer/mirrordir.php")
MYSQL_DIR       = os.path.normpath("//olympic.colorado.edu/c$/Program Files/MySQL/MySQL Server 5.1/bin/")
MYSQL_HOST      = "assettdev.colorado.edu"
ASSETTTEST_URL  = "assetttest.colorado.edu"
PASSWORD_LENGTH = 4
SCRIPT_DIR      = "/"


def main():
    global PRODUCTION_DIR
    global DEVELOPMENT_DIR
    global SCRIPT_DIR

    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

    # Make sure the user specified a directory to mirror
    if len(sys.argv) < 4:
        print("Not enough arguments. Usage: assettdev.py website sql_username sql_password")
        sys.exit()

    # Set directories to the user specified directory
    target = sys.argv[1]
    target_dir = "{}.colorado.edu".format(sys.argv[1])
    mysql_creds = {'user': sys.argv[2], 'pass': sys.argv[3]}

    mirror_web_dir(target, target_dir)
    table_name = mirror_db(target, mysql_creds)
    # If there is a database, create a user and update the old URLS
    if table_name:
        create_user(table_name, mysql_creds)
        update_database(target, target_dir, table_name, mysql_creds)
    run_drush(target_dir, target)
    run_callpermalink(target)
    log("assettdev.py completed.")


# Print a message to the terminal that includes the current time and message
def log(message):
    now = time.strftime("%I:%M:%S")
    print("{} - {}".format(now, message))


# Use proteus.php to generate a password that is PASSWORD_LENGTH words long.
def randpass():
    os.chdir(PROTEUS_DIR)
    proc = subprocess.Popen("php {} -randpass {}".format(PROTEUS_PHP, PASSWORD_LENGTH), stdout=subprocess.PIPE)
    return proc.stdout.read().decode('ascii').rstrip()[15:]


# Execute Proteus (PROTEUS_PHP) on directory DEVELOPMENT_DIR to change passwords and setup setting.php file
def run_proteus_default():
    # Run Proteus with -default flag
    os.chdir(PROTEUS_DIR)
    proc = subprocess.Popen("php {} -default {}".format(PROTEUS_PHP, DEVELOPMENT_DIR), stdout=subprocess.PIPE)
    log(proc.stdout.read().decode('ascii'))


# Execute Proteus (PROTEUS_PHP) with -adminpass flag followed by passmove.cmd
def run_proteus_admin():
    # Run Proteus with -adminpass flag
    os.chdir(PROTEUS_DIR)
    proc = subprocess.Popen("php {} -adminpass".format(PROTEUS_PHP), stdout=subprocess.PIPE)
    log(proc.stdout.read().decode('ascii'))


def treecopy_ignore(dir, files):
    return {".htaccess"}


# Mirror target_dir into DEVELOPMENT_DIR (Objective #1)
def mirror_web_dir(target, target_dir):
    drupal_dir = os.path.normpath(PRODUCTION_DIR + '/drupalbase')
    prod_dir = os.path.normpath(PRODUCTION_DIR + '/' + target_dir)
    dev_dir = os.path.normpath(DEVELOPMENT_DIR + '/' + target)

    log("Starting mirror process...");
    proc = subprocess.Popen("php {} {} {} {}".format(MIRRORDIR_PATH, drupal_dir, prod_dir, dev_dir), stdout=subprocess.PIPE)
    log(proc.stdout.read().decode('ascii'))


# Import the target db dump into the test sql database (Objective #2)
def mirror_db(target, mysql_creds):
    global DB_BACKUP_DIR

    # Get all folders from DB_BACKUP_DIR
    dirs = []
    for d in os.listdir(DB_BACKUP_DIR):
        d = os.path.normpath(DB_BACKUP_DIR + '/' + d)
        if os.path.isdir(d):
            dirs.append(d)

    # Sort the folders by creation time and return the most recently created directory
    DB_BACKUP_DIR = sorted(dirs, key=lambda x: os.path.getctime(x), reverse=True)[0]
    DB_BACKUP_DIR = os.path.normpath(DB_BACKUP_DIR)

    # Find specific db dump file
    os.chdir(DB_BACKUP_DIR)
    dbfile = glob.glob('*_*_{}.sql'.format(target));

    if len(dbfile): 
        dbfile = dbfile[0]

        # Cut the ends of the file name to get the table name
        table_name = dbfile[3:-4]

        # Import dump into MYSQL_HOST
        log("Attemping import of {} dump to {}.".format(dbfile, MYSQL_HOST))
        input = open(os.path.normpath(dbfile))
        mysql_bin = os.path.normpath(MYSQL_DIR + '/' + 'mysql')
        mysql_args = [mysql_bin, "--host=%s" % MYSQL_HOST, "--user=%s" % mysql_creds.get('user'), "--password=%s" % mysql_creds.get('pass'), "--max_allowed_packet=1073741824"]

        proc = subprocess.Popen(mysql_args, stdin=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        out, err = out.decode('ascii'), err.decode('ascii')

        if len(err):
            log("Failed to import db dump. Error: {}".format(err))
        else:
            log("Successfully imported db dump to {}.".format(MYSQL_HOST))

        return table_name

    else:
        log("No database dump found.")
        return None


def create_user(table_name, mysql_creds):
    user = table_name

    # Generate a new password
    password = randpass()
    log("Password: {}".format(password))

    # Truncate the username if it's longer than 14 chars
    if len(user) > 16:
        user = user[:16]

    # SQL commands to be executed on the database
    # These commands delete an existing user if it exists and then 
    # creates a new user and grants them USER_PRIVS defined privileges.
    commands = [
                "GRANT USAGE ON *.* TO '{}'@'localhost' IDENTIFIED BY '{}';".format(user, user),
                "DROP USER '{}'@'localhost';".format(user),
                "FLUSH PRIVILEGES;",
                "CREATE USER '{}'@'localhost' IDENTIFIED BY '{}';".format(user, password),
                "GRANT {} ON {}.* TO '{}'@'localhost' WITH GRANT OPTION;".format(USER_PRIVS, table_name, user)
               ]

    log("Attemping to create user {} for {} database.".format(user, table_name))

    curr_dir = os.getcwd()
    os.chdir(MYSQL_DIR)
    mysql_args = ["mysql", "--host=%s" % MYSQL_HOST, "--user=%s" % mysql_creds.get('user'), "--password=%s" % mysql_creds.get('pass')]
    proc = subprocess.Popen(mysql_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for command in commands:
        proc.stdin.write(bytes(command.encode('ascii')))

    # Read output and error from subprocess
    out, err = proc.communicate()
    out, err = out.decode('ascii'), err.decode('ascii')

    # If there was an error
    if len(err):
        log("Failed to create user. Error: {}".format(err))
    else:
        log("Successfully created user {}.".format(table_name))


def update_database(target, old_domain, table_name, mysql_creds):
    log("Updating database links")
    os.chdir(SCRIPT_DIR)
    replace = ASSETTTEST_URL + '/' + target
    srdb_args = ["php", "srdb.cli.php", "-h", MYSQL_HOST, "-n", table_name, "-u", mysql_creds.get('user'), "-p", mysql_creds.get('pass'), "-s", old_domain, "-r", replace]
    proc = subprocess.Popen(srdb_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = proc.communicate()
    out, err = out.decode('ascii'), err.decode('ascii')
    
    # Uncomment these lines to print output of srdb.cli.php
    #log("Output: {}\n".format(out))
    #log("Error: {}\n".format(err))

    log("update_database completed.")

    run_proteus_default()
    run_proteus_admin()


def run_drush(target_dir, target):
    # Check if directory is a Drupal website
    if os.path.islink(os.path.normpath(PRODUCTION_DIR + '/' + target_dir + '/includes')) and os.path.islink(os.path.normpath(PRODUCTION_DIR + '/' + target_dir + '/modules')):
        log("Drupal detected. Running drush.")
        os.chdir(SCRIPT_DIR)
        proc = subprocess.Popen("php drush.php {}".format(target), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = proc.communicate()
        out, err = out.decode('ascii'), err.decode('ascii')

        if len(out):
            log("Output: {}\n".format(out))
        if len(err):
            log("Error: {}\n".format(err))


def run_callpermalink(target):
    log("Running callpermalink")
    os.chdir(SCRIPT_DIR)
    log(target)
    call = "php callpermalink.php assetttest.colorado.edu/{} \"/%postname%/\"".format(target)
    log(call)
    proc = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = proc.communicate()
    out, err = out.decode('ascii'), err.decode('ascii')

    if len(out):
        log("Output: {}\n".format(out))
    if len(err):
        log("Error: {}\n".format(err))


# Start the program
if __name__ == "__main__":
    main()
    