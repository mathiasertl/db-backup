# backup MySQL databases to a local directory:
#10 *	* * * 	root	dbdump --backend=mysql --datadir=/backup/mysql/

# backup PostgreSQL databases to a remote location. Dumps are signed and
# encrypted using GPG:
#0  *	* * *	root 	dbdump --backend=postgresql --datadir=/backup/postgres/mars --su=postgres --remote=backup-postgres-mars@backup.example.com --sign=root@example.com --encrypt=backup
