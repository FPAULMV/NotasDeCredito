USE [Sinergia_Aux]
GO

/****** Object:  Table [dbo].[Test_CreditNoteVendor]    Script Date: 27/01/2025 11:31:23 a. m. ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[CreditNoteVendor](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[VendorId] [int] NOT NULL,
	[StationId] [int] NOT NULL,
	[Date] [datetime] NOT NULL,
	[ProductName] [nvarchar](255) NOT NULL,
	[Remision] [nvarchar](255) NULL,
	[Invoice] [nvarchar](255) NULL,
	[CreditNoteNumber] [nvarchar](255) NULL,
	[TarTad] [nvarchar](255) NULL,
	[Tax] [decimal](18, 2) NOT NULL,
	[Total] [decimal](18, 2) NOT NULL,
	[DestinationName] [nvarchar](255) NULL,
	[FiscalFolio] [nvarchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO


