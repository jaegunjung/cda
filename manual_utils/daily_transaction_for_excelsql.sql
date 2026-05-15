
 SELECT FORMAT([Date], 'MM/dd/yyyy') as Date
      ,[Open_Price_USD]
  FROM [cda].[dbo].[CryptoDaily]
  where Crypto = 'BTC' and date >= '2024-11-10'