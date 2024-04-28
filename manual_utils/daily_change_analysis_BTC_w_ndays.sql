drop table if exists #date_chg_grp
-- drop table #date_chg_grp

select Date, [Open_Price_USD], change_per,
       case when 30 < change_per and change_per <= 40 then 40
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
into #date_chg_grp
from
(select Date, [Open_Price_USD], [Prev_Open_Price_USD], ([Open_Price_USD]-[Prev_Open_Price_USD])/[Prev_Open_Price_USD] * 100 as change_per
from
(SELECT [Date]
      ,[Open_Price_USD]
      ,lag([Open_Price_USD]) over (order by Date) as [Prev_Open_Price_USD]
  FROM [cda].[dbo].[CryptoDaily]) a
) b

-- drop table ndays_gt_4pct
select datediff(day, Prev_Date, Date) as n_days, *
into ndays_gt_4pct
from
(select Date, lag(Date) over (order by Date) as [Prev_Date], chg_per_group, lag(chg_per_group) over (order by Date) as [prev_chg_per_group], [Open_Price_USD], change_per 
from #date_chg_grp 
where chg_per_group >= 6) a

-- drop table ndays_gt_4pct
select datediff(day, Prev_Date, Date) as n_days, *
into ndays_gt_m4pct
from
(select Date, lag(Date) over (order by Date) as [Prev_Date], chg_per_group, lag(chg_per_group) over (order by Date) as [prev_chg_per_group], [Open_Price_USD], change_per 
from #date_chg_grp 
where chg_per_group <= -4) a