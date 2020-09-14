# MP Takehome Assignment

## Requirements

1. Python3
2. Environment Variables must be set
   - `SMTP_ADDRESS` email address for login to smtp
   - `SMTP_PASSWORD` password for login to smtp server
3. Install python3 dependencies
   ```bash
   pip3 install -r requirements.txt
   ```
   
4. AWS Credentials with Access to the S3 bucket (or an EC2 role)

## Configuring
 Modify the parameters in script (These could have been passed as arguments)
   - `BACKUP_TIME` The hour and minute ("HH:MM") to run the backup e.g. "00:00"
   - `BACKUP_DIR` The system directory to backup
   - `BACKUP_S3_BUCKET` The S3 buckets to upload the backup
   - `BACKUP_FILENAME` The prefix name for the backup archive file
   - `BACKUP_STORAGE_DIR` A local directory to store the archive file temporarily 
   - `BACKUP_RETENTION_DAYS` Number of days to retain backups in S3
   - `SMTP_SERVER` The smtp relay server e.g. `smtp.gmail.com`
   
## Running
```bash
python3 backup.py &
```

