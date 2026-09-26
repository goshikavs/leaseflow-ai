# Local Setup

## Prerequisites

- .NET 8 SDK
- Docker Desktop
- Azure Service Bus namespace
- Azure Key Vault
- Azure Cosmos DB account

## Restore, Build, Test

```bash
dotnet restore InsurancePlatform.sln
dotnet build InsurancePlatform.sln
dotnet test InsurancePlatform.sln
```

## EF Core Migrations

Create initial migrations after installing the SDK:

```bash
dotnet ef migrations add InitialIdentity --project src/Services/Identity/Insurance.Services.Identity
dotnet ef migrations add InitialPolicy --project src/Services/Policy/Insurance.Services.Policy
dotnet ef migrations add InitialRating --project src/Services/Rating/Insurance.Services.Rating
dotnet ef migrations add InitialCoverage --project src/Services/Coverage/Insurance.Services.Coverage
dotnet ef migrations add InitialCustomer --project src/Services/Customer/Insurance.Services.Customer
dotnet ef migrations add InitialClaims --project src/Services/Claims/Insurance.Services.Claims
dotnet ef migrations add InitialBilling --project src/Services/Billing/Insurance.Services.Billing
```

The services call `Database.MigrateAsync()` on startup so the generated migrations will apply automatically per environment.
