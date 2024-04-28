select avg(change_per) as avg_change_per, avg(abs(change_per)) as avg_abs_change_per, 
max(change_per) as max_change_per, min(change_per) as min_change_per, min(abs(change_per)) as min_abs_change_per,
max(abs(change_per)) as max_abs_change_per
from (
select Date, [Open_Price_USD], [Prev_Open_Price_USD], ([Open_Price_USD]-[Prev_Open_Price_USD])/[Prev_Open_Price_USD] * 100 as change_per
from
(SELECT [Date]
      ,[Open_Price_USD]
      ,lag([Open_Price_USD]) over (order by Date) as [Prev_Open_Price_USD]
  FROM [cda].[dbo].[CryptoDaily] where Crypto = 'BTC') a
) b