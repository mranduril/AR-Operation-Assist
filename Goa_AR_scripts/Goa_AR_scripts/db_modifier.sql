use AR_GOA_POC;
GO



--EXECUTE dbo.create_component -2, N'TEST', N'TEST_VENDOR', N'TEST_IMAGE', N'/user/documents';
--GO

--EXECUTE dbo.count_connections;
EXEC sp_configure filestream_access_level, 2
RECONFIGURE
