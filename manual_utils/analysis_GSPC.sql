
drop table #yr_open_price
drop table #yr_close_price

SELECT FORMAT([Date], 'yyyy') as [Year]
      ,[Open_Price_USD]
into #yr_open_price
  FROM [cda].[dbo].[StockDaily]
  where Symbol = '^GSPC'
and FORMAT([Date], 'yyyy-MM-dd') in 
('2014-01-02', '2015-01-02', '2016-01-04', '2017-01-03', '2018-01-02',
'2019-01-02', '2020-01-02', '2021-01-04', '2022-01-03', '2023-01-03')

SELECT FORMAT([Date], 'yyyy') as [Year]
      ,[Close_Price_USD]
into #yr_close_price
  FROM [cda].[dbo].[StockDaily]
  where Symbol = '^GSPC'
  and SUBSTRING(FORMAT([Date], 'MM-dd'), 1, 5) in ('12-29', '12-30', '12-31')
and FORMAT([Date], 'yyyy-MM-dd') in 
('2014-12-31', '2015-12-31', '2016-12-30', '2017-12-29', '2018-12-31',
'2019-12-31', '2020-12-31', '2021-12-31', '2022-12-30')

select o.year, o.Open_Price_USD, c.Close_Price_USD, (c.Close_Price_USD/o.Open_Price_USD -1) * 100 as APR_per
into Anal_ann_GSPC
from #yr_open_price o
left join #yr_close_price c on o.year = c.year

-- Comparison BTC vs GSPC
select s.year, s.APR_per as GSPC_APR_per, b.APR_per as BTC_APR_per, b.APR_per/s.APR_per as BTC_over_GSPC
from Anal_ann_GSPC s
left join Anal_ann_BTC b on s.Year = b.Year