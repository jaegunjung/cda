/*
-- If string_split is not recognized, run below.

SELECT compatibility_level
FROM sys.databases
WHERE name = 'cda';

ALTER DATABASE cda
SET COMPATIBILITY_LEVEL = 130;
*/

drop table if exists #tickers
drop table if exists #mo_beg_end_dates
drop table if exists #mo_open_price
drop table if exists #mo_close_price

declare @input_str varchar(1000) = '^GSPC,^DJI,AMZN,ENVX,AAPL,VFIAX,TSLA,QQQ,META,GOOG,ENVX,QQQ,NVDA'

-- Insert the parsed values into the temp table using STRING_SPLIT
select value
into #tickers
from string_split(@input_str, ',');

select FORMAT(min(Date), 'yyyy-MM-dd') as beg_date, FORMAT(max(Date), 'yyyy-MM-dd') as end_date
into #mo_beg_end_dates
from
(SELECT [Date], FORMAT([Date], 'yyyy-MM') as mmdd
  FROM [cda].[dbo].[StockDaily]
  where Symbol = '^GSPC' and Date >= '2013-05-01 00:00:00.0000000 -07:00' and Date <= '2023-11-30 00:00:00.0000000 -08:00') a
group by mmdd

SELECT Symbol, FORMAT([Date], 'yyyy-MM') as [YearMo]
      ,[Open_Price_USD]
into #mo_open_price
  FROM [cda].[dbo].[StockDaily]
  where (Symbol in (select value from #tickers)
  and FORMAT([Date], 'yyyy-MM-dd') in 
  (select beg_date from #mo_beg_end_dates))
  or (Symbol = 'ENVX' and FORMAT([Date], 'yyyy-MM-dd') = '2021-01-05')

SELECT Symbol, FORMAT([Date], 'yyyy-MM') as [YearMo]
      ,[Close_Price_USD]
into #mo_close_price
  FROM [cda].[dbo].[StockDaily]
  where Symbol in (select value from #tickers)
  and FORMAT([Date], 'yyyy-MM-dd') in 
  (select end_date from #mo_beg_end_dates)

select o.Symbol, o.YearMo, o.Open_Price_USD, c.Close_Price_USD, (c.Close_Price_USD/o.Open_Price_USD -1) * 100 as rate_per
into Anal_mon_stocks
from #mo_open_price o
left join #mo_close_price c on o.YearMo = c.YearMo and o.Symbol = c.Symbol

select * from Anal_mon_stocks
where Symbol in ('^GSPC','^DJI','AMZN','ENVX','AAPL','TSLA','GOOG', 'ENVX', 'META', 'QQQ', 'NVDA')
order by Symbol, YearMo