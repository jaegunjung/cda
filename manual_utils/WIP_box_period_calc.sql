WITH PriceComparisons AS (
    SELECT
        Date,
        Open_Price_USD,
        Total_Volume_USD,
        LAG(Open_Price_USD, 1, Open_Price_USD) OVER (ORDER BY Date) AS PrevPrice, -- default to current price if there is no previous price
        AVG(Total_Volume_USD) OVER (ORDER BY Date) AS AvgVolume -- moving average of the volume
		/*,Total_Volume_USD*/
    FROM
        #CryptoDailytmp
),
PriceChanges AS (
    SELECT
        *,
        CASE
            WHEN Open_Price_USD <= PrevPrice * 1.03 AND Open_Price_USD >= PrevPrice * 0.97 THEN 0
            ELSE 1
        END AS PriceChangeFlag
    FROM
        PriceComparisons
),
GroupedPriceChanges AS (
    SELECT
        *,
        SUM(PriceChangeFlag) OVER (ORDER BY Date) AS PriceGroup
    FROM
        PriceChanges
),
FilteredGroups AS (
    SELECT
        Date,
        Open_Price_USD,
        Total_Volume_USD,
        AvgVolume,
        PriceGroup,
        COUNT(*) OVER (PARTITION BY PriceGroup) AS GroupSize
    FROM
        GroupedPriceChanges
    WHERE
        /*Total_Volume_USD < AvgVolume AND */PriceChangeFlag = 0
),
BoxRanges AS (
    SELECT
        MIN(Date) AS BoxStart,
        MAX(Date) AS BoxEnd,
        COUNT(*) AS DaysCount
    FROM
        FilteredGroups
    GROUP BY
        PriceGroup
    HAVING
        COUNT(*) >= 5 -- This number represents the minimum number of days to consider as a box range
)

SELECT BoxStart, BoxEnd, DaysCount
FROM BoxRanges
ORDER BY BoxStart;
