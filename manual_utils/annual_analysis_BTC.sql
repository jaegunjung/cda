/****** 
First Halving: November 28, 2012
Second Halving: July 9, 2016
Third Halving: May 11, 2020
Fourth Halving: Apr 19, 2024
******/

drop table if exists #btc_yr

-- Get the 1/1 data
SELECT Date, [Open_Price_USD]
into #btc_yr
FROM [cda].[dbo].[CryptoDaily]
WHERE SUBSTRING(FORMAT([Date], 'MM-dd'), 1, 5) = '01-01'

-- Calculate APR
select FORMAT([Date], 'yyyy') as [Year], Open_Price_USD, Yr_end_Price, (Yr_end_Price/Open_Price_USD -1) * 100 as APR_per
into Anal_ann_BTC
from
(select Date, Open_Price_USD, lead(Open_Price_USD) over (order by Date) as Yr_end_Price 
from #btc_yr) a