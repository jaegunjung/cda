/*
-- If string_split is not recognized, run below.

SELECT compatibility_level
FROM sys.databases
WHERE name = 'cda';

ALTER DATABASE cda
SET COMPATIBILITY_LEVEL = 130;
*/

drop table if exists #yr_open_price
drop table if exists #yr_close_price
drop table if exists #tickers

declare @input_str varchar(1000) = '^GSPC,^DJI,AMZN,ENVX,AAPL,VFIAX,TSLA,QQQ,META,GOOG,ENVX,QQQ,NVDA'

-- Insert the parsed values into the temp table using STRING_SPLIT
select value
into #tickers
from string_split(@input_str, ',');

SELECT Symbol, FORMAT([Date], 'yyyy') as [Year]
      ,[Open_Price_USD]
into #yr_open_price
  FROM [cda].[dbo].[StockDaily]
  where (Symbol in (select value from #tickers)
and FORMAT([Date], 'yyyy-MM-dd') in 
('2014-01-02', '2015-01-02', '2016-01-04', '2017-01-03', '2018-01-02',
'2019-01-02', '2020-01-02', '2021-01-04', '2022-01-03', '2023-01-03'))
or (Symbol = 'ENVX' and FORMAT([Date], 'yyyy-MM-dd') = '2021-01-05')

SELECT Symbol, FORMAT([Date], 'yyyy') as [Year]
      ,[Close_Price_USD]
into #yr_close_price
  FROM [cda].[dbo].[StockDaily]
  where Symbol in (select value from #tickers)
  and SUBSTRING(FORMAT([Date], 'MM-dd'), 1, 5) in ('12-29', '12-30', '12-31')
and FORMAT([Date], 'yyyy-MM-dd') in 
('2014-12-31', '2015-12-31', '2016-12-30', '2017-12-29', '2018-12-31',
'2019-12-31', '2020-12-31', '2021-12-31', '2022-12-30')

select o.Symbol, o.year, o.Open_Price_USD, c.Close_Price_USD, (c.Close_Price_USD/o.Open_Price_USD -1) * 100 as APR_per
into Anal_ann_stocks
from #yr_open_price o
left join #yr_close_price c on o.year = c.year and o.Symbol = c.Symbol

select * from Anal_ann_stocks
where Symbol in ('^GSPC','^DJI','AMZN','ENVX','AAPL','TSLA','GOOG', 'ENVX', 'META', 'QQQ', 'NVDA') and year between 2020 and 2023
order by Symbol, year
