/****** 
First Halving: November 28, 2012
Second Halving: July 9, 2016
Third Halving: May 11, 2020
Fourth Halving: Apr 19, 2024
******/

drop table if exists #btc_mo

-- Get the first day of each month data
SELECT Date, [Open_Price_USD]
into #btc_mo
FROM [cda].[dbo].[CryptoDaily]
WHERE SUBSTRING(FORMAT([Date], 'MM-dd'), 3, 5) = '-01'

-- Calculate APR
select FORMAT([Date], 'yyyy-MM') as [YearMo], Open_Price_USD, Mo_end_Price, (Mo_end_Price/Open_Price_USD -1) * 100 as rate_per
into Anal_mon_BTC
from
(select Date, Open_Price_USD, lead(Open_Price_USD) over (order by Date) as Mo_end_Price 
from #btc_mo) a

select * from Anal_mon_BTC