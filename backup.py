import os
import syslog
import datetime
import boto3
import time
import sys
import smtplib, ssl

###########################################################
# * INPUT PARAMETERS                                      #
###########################################################
BACKUP_TIME = "23:46"
BACKUP_DIR = "/Users/andymedina/personal/mparticle/"
BACKUP_S3_BUCKET = "mparticle-takehome-assignment"
BACKUP_FILENAME = "backup"
BACKUP_STORAGE_DIR = "/tmp/"
BACKUP_RETENTION_DAYS = 7


###########################################################
###########################################################


def upload(file, filepath, bucket):
    s3 = boto3.resource('s3')

    try:
        s3.meta.client.upload_file(filepath + file, bucket, file)
        print('Uploaded ' + file + ' to s3://' + bucket)
    except:
        print('Backup upload failed: ', sys.exc_info()[0])


# An alternative would be to set the bucket lifecycle to 7 days
def purge_old(days, bucket):
    s3 = boto3.client('s3')
    purge_list = []
    try:
        objects = s3.list_objects_v2(Bucket=bucket)

        # Create list of old backup keys
        for backup in objects['Contents']:
            if datetime.datetime.today() - backup['LastModified'] > days:
                purge_list.append({'Key': backup['Key']})

        # Delete old keys
        response = s3.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': purge_list
            }
        )
        print(response)
    except:
        print("Could not purge old backups: ", sys.exc_info()[0])


def make_tar(file, dest, source):
    try:
        # Create gzipped tarball
        os.system("tar -cpzf " + dest + file + " " + source)
    except:
        print("Backup creation failed: ", sys.exc_info()[0])

    print("Backup created " + dest + file)


def validate(file, path, bucket):
    s3 = boto3.client('s3')

    try:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=file
        )
        backup = response['Contents'][0]
    except:
        print("Could not list s3 objects")
        return False

    original_size = os.stat(path + file).st_size
    backup_size = backup['Size']
    backup_name = backup['Key']

    if backup_name == file and original_size == backup_size:
        return True

    return False


def email(status, message):
    port = 465
    password = os.getenv('EMAIL_PASSWORD')
    sender_email = os.getenv('EMAIL_ADDRESS')
    receiver_email = 'andymedinajr@gmail.com'
    message = "\nSubject: Backup " + status + "\n\n" + message

    # Create a secure SSL context
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

    except Exception as e:
        print(e)


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
        purge_old(BACKUP_RETENTION_DAYS)

        # Upload new backup tarball to S3
        upload(filename, BACKUP_STORAGE_DIR, BACKUP_S3_BUCKET)

        # Validate Backup
        if validate(filename, BACKUP_STORAGE_DIR, BACKUP_S3_BUCKET):
            email('Success')
        else:
            email('Failed')

        # Sleep to prevent running again within a minute
        time.sleep(60)