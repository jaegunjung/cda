
select FORMAT(min(Date), 'yyyy-MM-dd') as beg_date, FORMAT(max(Date), 'yyyy-MM-dd') as end_date
into #mo_beg_end_dates
from
(SELECT [Date], FORMAT([Date], 'yyyy-MM') as mmdd
  FROM [cda].[dbo].[StockDaily]
  where Symbol = '^GSPC' and Date >= '2013-05-01 00:00:00.0000000 -07:00' and Date <= '2023-11-30 00:00:00.0000000 -08:00') a
group by mmdd
