DECLARE @TBLNAME VARCHAR(255)
SET @TBLNAME = 'CryptoDaily'

DECLARE @CREATE_TEMPLATE VARCHAR(MAX)
SET @CREATE_TEMPLATE = 
'
CREATE TABLE  {TBLNAME} (
    ID int IDENTITY(1,1) primary key,
	Crypto nvarchar(50) NOT NULL,
	[Date] datetimeoffset (7) NOT NULL,
	Open_Price_USD decimal(20,2) NOT NULL,
	Total_Volume_USD decimal(30,2) NOT NULL,
	Market_Cap_USD decimal(38,2) NOT NULL,
	DateTmModified datetimeoffset (7) default SYSDATETIMEOFFSET(),
)
CREATE UNIQUE INDEX uidx_CryptoDaily on {TBLNAME} (Crypto, [Date]);
'
DECLARE @SQL_SCRIPT VARCHAR(MAX)

IF NOT EXISTS (SELECT * FROM SYSOBJECTS WHERE NAME=@TBLNAME AND XTYPE='U')
BEGIN
	SET @SQL_SCRIPT = REPLACE(@CREATE_TEMPLATE, '{TBLNAME}', @TBLNAME)
	EXECUTE (@SQL_SCRIPT)
END;