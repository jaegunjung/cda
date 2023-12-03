DECLARE @DBNAME VARCHAR(255)
SET @DBNAME = 'cda'

DECLARE @CREATE_TEMPLATE VARCHAR(MAX)
DECLARE @COMPAT_TEMPLATE VARCHAR(MAX)
DECLARE @RECOVERY_TEMPLATE VARCHAR(MAX)

SET @CREATE_TEMPLATE = 'CREATE DATABASE {DBNAME}'
/* About COMPATIBILITY_LEVEL
https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level?view=sql-server-ver16
*/
SET @COMPAT_TEMPLATE='ALTER DATABASE {DBNAME} SET COMPATIBILITY_LEVEL = 100'
/* RECOVERY SIMPLE automatically removes the transaction log records on every completed transaction. 
https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/recovery-models-sql-server?view=sql-server-ver16
*/
SET @RECOVERY_TEMPLATE='ALTER DATABASE {DBNAME} SET RECOVERY SIMPLE'

DECLARE @SQL_SCRIPT VARCHAR(MAX)

IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = @dbname)
BEGIN
	SET @SQL_SCRIPT = REPLACE(@CREATE_TEMPLATE, '{DBNAME}', @DBNAME)
	EXECUTE (@SQL_SCRIPT)

	SET @SQL_SCRIPT = REPLACE(@COMPAT_TEMPLATE, '{DBNAME}', @DBNAME)
	EXECUTE (@SQL_SCRIPT)

	SET @SQL_SCRIPT = REPLACE(@RECOVERY_TEMPLATE, '{DBNAME}', @DBNAME)
	EXECUTE (@SQL_SCRIPT)
END;