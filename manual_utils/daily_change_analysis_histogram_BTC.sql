drop table if exists #btc_chg_hist
drop table if exists #btc_all_cnt

select chg_per_group as cpg, count(*) as cnt
into #btc_chg_hist
from 
(select case when 30 < change_per and change_per <= 40 then 40
            when 20 < change_per and change_per <= 30 then 30
			when 10 < change_per and change_per <= 20 then 20
			when 8 < change_per and change_per <= 10 then 10
			when 6 < change_per and change_per <= 8 then 8
			when 4 < change_per and change_per <= 6 then 6
			when 2 < change_per and change_per <= 4 then 4
			when 1 < change_per and change_per <= 2 then 2
			when -1 < change_per and change_per <= 1 then 1
			when -2 < change_per and change_per <= -1 then -1
			when -4 < change_per and change_per <= -2 then -2
			when -6 < change_per and change_per <= -4 then -4
			when -8 < change_per and change_per <= -6 then -6
			when -10 < change_per and change_per <= -8 then -8
			when -20 < change_per and change_per <= -10 then -10
			when -30 < change_per and change_per <= -20 then -20
			when -40 < change_per and change_per <= -30 then -30
       end as chg_per_group
from
(select Date, [Open_Price_USD], [Prev_Open_Price_USD], ([Open_Price_USD]-[Prev_Open_Price_USD])/[Prev_Open_Price_USD] * 100 as change_per
from
(SELECT [Date]
      ,[Open_Price_USD]
      ,lag([Open_Price_USD]) over (order by Date) as [Prev_Open_Price_USD]
  FROM [cda].[dbo].[CryptoDaily]) a
) b 
) c
group by chg_per_group
order by chg_per_group

select sum(cnt) as all_cnt
into #btc_all_cnt
from #btc_chg_hist

select cpg as change_per_group, cnt, cast(cnt as float)/all_cnt * 100. as perc
from #btc_chg_hist
left join #btc_all_cnt on 1=1
order by cpg desc
