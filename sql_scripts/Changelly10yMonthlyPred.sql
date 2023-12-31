DECLARE @TBLNAME VARCHAR(255)
SET @TBLNAME = 'Changelly10yMonthlyPred'

DECLARE @CREATE_TEMPLATE VARCHAR(MAX)
SET @CREATE_TEMPLATE =
'
CREATE TABLE  {TBLNAME} (
    ID int IDENTITY(1,1) primary key,
	Crypto nvarchar(50) NOT NULL,
	Date_Pred datetimeoffset (7) NOT NULL,
	[Month] datetimeoffset (7) NOT NULL,
	Min_Close_Price_USD decimal(20,2) NOT NULL,
	Avg_Close_Price_USD decimal(20,2) NOT NULL,
	Max_Close_Price_USD decimal(20,2) NOT NULL,
	DateTmModified datetimeoffset (7) default SYSDATETIMEOFFSET(),
)
CREATE UNIQUE INDEX uidx_Changelly10yMonthlyPred on {TBLNAME} (Crypto, Date_Pred, [Month]);
'
DECLARE @SQL_SCRIPT VARCHAR(MAX)

IF NOT EXISTS (SELECT * FROM SYSOBJECTS WHERE NAME=@TBLNAME AND XTYPE='U')
BEGIN
	SET @SQL_SCRIPT = REPLACE(@CREATE_TEMPLATE, '{TBLNAME}', @TBLNAME)
	EXECUTE (@SQL_SCRIPT)
END;