DROP TABLE IF EXISTS #net;

-- Construct #net
SELECT 
    [type], 
    price * amount AS net, 
    [amount],
    LEFT(CONVERT(VARCHAR, [Date], 120), 7) AS [Month]  -- YYYY-MM 
INTO #net
FROM Transactions
WHERE [Date] >= '2023-12-01' AND [Date] <= '2024-04-30';

-- Monthly summary
SELECT
    [type],
    [Month],
    COUNT(*) AS cnt,
    SUM([amount]) AS sum_amount,
    SUM(net) / SUM([amount]) AS avg_price
FROM #net
GROUP BY [Month], [type]
ORDER BY [Month], [type];