## Requirements

1. daily backup of a filesystem directory to an existing s3 bucket
2. The backup time and date must appear in the backup file name.
3. The backup script should run once per day, automatically.
4. You must purge backups older 7 days
5. You must monitor job status, confirm archive file exists in s3, and email a status message at the
end of the script run
6. The script must log to syslog or a dedicated logfile
7. Your solution must be published to a public repository for mParticle review.