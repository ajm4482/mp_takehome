import os
import datetime
import boto3
import time
import smtplib
import ssl
import logging as log
import subprocess

###########################################################
# * INPUT PARAMETERS                                      #
###########################################################
BACKUP_TIME = "19:09"
BACKUP_DIR = "/home/ubuntu/backup/"
BACKUP_S3_BUCKET = "mp-takehome-assignment"
BACKUP_FILENAME = "backup"
BACKUP_STORAGE_DIR = "/tmp/"
BACKUP_RETENTION_DAYS = 7
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_ADDRESS = os.getenv('SMTP_ADDRESS')
SMTP_SERVER = 'smtp.gmail.com'

###########################################################
# * LOGGING CONFIGURATION                                 #
##########################################################

log.basicConfig(filename=BACKUP_FILENAME + '.log', level=log.INFO, format='%(asctime)s %(message)s')


###############################################################
#  * UPLOADS A FILE IN THE SYSTEM DIRECTORY TO AN S3 BUCKET   #
###############################################################
def upload(file, filepath, bucket):
    s3 = boto3.resource('s3')

    try:
        s3.meta.client.upload_file(filepath + file, bucket, file)
        log.info('Uploading ' + file + ' to s3://' + bucket)
    except FileNotFoundError:
        log.error('Backup file not found')
    except:
        log.error('Backup upload failed')


###############################################################
# * PURGES OBJECTS IN AN S3 BUCKET OLDER THAN 'X' DAYS        #
###############################################################
# An alternative would be to set the bucket lifecycle to 7 days
def purge_old(days, bucket):
    s3 = boto3.client('s3')
    purge_list = []
    try:
        objects = s3.list_objects_v2(Bucket=bucket)
        # Create list of old backup keys
        for backup in objects['Contents']:
            if backup['LastModified'] < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days):
                purge_list.append({'Key': backup['Key']})

        # Delete keys if they exist
        if len(purge_list) > 0:
            response = s3.delete_objects(
                Bucket=bucket,
                Delete={
                    'Objects': purge_list
                }
            )
            log.info(response)
        else:
            log.info('Nothing to purge')
    except:
        log.error('Could not purge old backups')


############################################################
# * CREATES A ZIPPED TARBALL OF A SYSTEM DIRECTORY         #
# * AND STORES IT IN DESTINATION DIRECTORY                 #
############################################################
def make_tar(file, dest, source_dir):
    try:
        # Create gzipped tarball
        subprocess.call(['tar', '-cpzf', dest + file, source_dir])
        log.info('Backup created ' + dest + file)
    except:
        log.error('Backup creation failed')


###########################################################
# * VALIDATES THE EXISTENCE OF A FILE IN AN S3 BUCKET     #
# * ALSO CHECKS FOR MATCHING FILE SIZE                    #
###########################################################
def validate(file, path, bucket):
    s3 = boto3.client('s3')

    # Retrieve Bucket contents with file name
    try:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=file
        )
        backup = response['Contents'][0]

        original_size = os.stat(path + file).st_size
        backup_size = backup['Size']
        backup_name = backup['Key']

        # Check if file exists and same size
        if backup_name == file and original_size == backup_size:
            return True

    except:
        log.error('Could not validate file in S3')

    return False


###########################################################
# * EMAILS A STATUS AND MESSAGE TO AN ADDRESS             #
###########################################################
def email(status, message, receiver):
    port = 465
    password = SMTP_PASSWORD
    sender_email = SMTP_ADDRESS
    receiver_email = receiver
    message = "\nSubject: Backup " + status + "\n\n" + message

    context = ssl.create_default_context()

    try:
        # Send Email
        with smtplib.SMTP_SSL(SMTP_SERVER, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

        log.info('Notification sent to: ' + receiver_email)
    except:
        log.warning('Notification failed to send')


###########################################################
# * MAIN SCRIPT                                           #
###########################################################
backup_hour = BACKUP_TIME.split(":")[0]
backup_minute = BACKUP_TIME.split(":")[1]

# An alternative to the infinite while loop is to use the cron daemon
while True:
    today = datetime.datetime.today()
    current_hour = today.strftime("%H")
    current_minute = today.strftime("%M")

    if current_hour == backup_hour and current_minute == backup_minute:
        # Backup filename with timestamp
        filename = BACKUP_FILENAME + "-" + today.strftime("%Y%m%d-%H%M%S") + ".tar.gz"

        # Create gzipped tarball of directory
        make_tar(filename, BACKUP_STORAGE_DIR, BACKUP_DIR)

        # Purge old backups in S3
        purge_old(BACKUP_RETENTION_DAYS, BACKUP_S3_BUCKET)

        # Upload new backup tarball to S3
        upload(filename, BACKUP_STORAGE_DIR, BACKUP_S3_BUCKET)

        # Allow for file to replicate in S3
        time.sleep(30)

        # Validate Backup
        if validate(filename, BACKUP_STORAGE_DIR, BACKUP_S3_BUCKET):
            email('Succeeded', 'Backup Process', 'andymedina@utexas.edu')
        else:
            email('Failed', 'Backup Process', 'andymedina@utexas.edu')

        # Sleep to prevent running again within a minute
        time.sleep(60)