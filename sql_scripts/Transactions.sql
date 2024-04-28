DECLARE @TBLNAME VARCHAR(255)
SET @TBLNAME = 'Transactions'

DECLARE @CREATE_TEMPLATE VARCHAR(MAX)
SET @CREATE_TEMPLATE = 
'
CREATE TABLE  {TBLNAME} (
    ID int IDENTITY(1,1) primary key,
	Symbol nvarchar(50) NOT NULL,
	[Date] datetimeoffset (7) NOT NULL,
	type nvarchar(50) NOT NULL,
	amount real NOT NULL,
	price real NOT NULL,
	fee real NOT NULL,
	DateTmModified datetimeoffset (7) default SYSDATETIMEOFFSET(),
)
'
DECLARE @SQL_SCRIPT VARCHAR(MAX)

IF NOT EXISTS (SELECT * FROM SYSOBJECTS WHERE NAME=@TBLNAME AND XTYPE='U')
BEGIN
	SET @SQL_SCRIPT = REPLACE(@CREATE_TEMPLATE, '{TBLNAME}', @TBLNAME)
	EXECUTE (@SQL_SCRIPT)
END;
