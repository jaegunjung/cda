DECLARE @TBLNAME VARCHAR(255)
SET @TBLNAME = 'ChangellyDailyMetrics'

DECLARE @CREATE_TEMPLATE VARCHAR(MAX)
SET @CREATE_TEMPLATE =
'
CREATE TABLE  {TBLNAME} (
	Crypto nvarchar(50) NOT NULL,
	Date_Pred datetimeoffset (7) NOT NULL,
	Price_USD decimal(20,2) NOT NULL,
	Change_24h_perc decimal(5,2) NOT NULL,
	Change_7d_perc decimal(5,2) NOT NULL,
	Market_Cap_USD decimal(38,2) NOT NULL,
	Circulating_Supply_BTC int NOT NULL,
	Trading_Volume_USD decimal(30,2) NOT NULL,
	All_Time_High decimal(30,2) NOT NULL,
	All_Time_Low decimal(5,2) NOT NULL,
	Price_Pred_7d_USD decimal(20,2) NOT NULL,
	Fear_Greed_Index int NOT NULL,
	Sentiment nvarchar(50) NOT NULL,
	Volatility_perc decimal(5,2) NOT NULL,
	GreenDays_30d_perc decimal(5,2) NOT NULL,
	SMA_50d_USD decimal(20,2) NOT NULL,
	SMA_200d_USD decimal(20,2) NOT NULL,
	RSI_14d decimal(20,2) NOT NULL,
	DateTmModified datetimeoffset (7) default SYSDATETIMEOFFSET(),
)
CREATE UNIQUE INDEX uidx_ChangellyDailyMetrics on {TBLNAME} ([Date_Pred]);
'
DECLARE @SQL_SCRIPT VARCHAR(MAX)

IF NOT EXISTS (SELECT * FROM SYSOBJECTS WHERE NAME=@TBLNAME AND XTYPE='U')
BEGIN
	SET @SQL_SCRIPT = REPLACE(@CREATE_TEMPLATE, '{TBLNAME}', @TBLNAME)
	EXECUTE (@SQL_SCRIPT)
END;