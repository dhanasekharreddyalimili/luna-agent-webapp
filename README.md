# Luna Foundry Agent Web App

A small Flask chat interface for an existing Microsoft Foundry agent, deployed to Linux Azure App Service with GitHub Actions.

## Project settings

The default configuration follows the supplied sample:

- Project endpoint: `https://msftfoundry202912.services.ai.azure.com/api/projects/AI-project1`
- Agent name: `luna-agent`

Override these values with App Service application settings if needed.

## Files

- `app.py` — Flask endpoints and Microsoft Foundry client integration
- `templates/index.html` — browser chat interface
- `requirements.txt` — Python dependencies
- `startup.sh` — Gunicorn startup command
- `.github/workflows/deploy.yml` — deploys on every push to `main`

## Push to GitHub

Create an empty GitHub repository, then run these commands from this folder in PowerShell:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial Luna agent web app"
git remote add origin https://github.com/YOUR_USERNAME/luna-agent-webapp.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. If the folder is already a Git repository, inspect `git status` and `git remote -v` before running `git init` or adding a remote.

## Create Azure App Service

Example commands for PowerShell; change the resource group, unique web app name, and region to your requirements:

```powershell
az login
$rg = "YOUR_RESOURCE_GROUP"
$app = "YOUR-UNIQUE-LUNA-APP-NAME"
$plan = "luna-agent-plan"
$location = "centralindia"

az group create --name $rg --location $location
az appservice plan create --name $plan --resource-group $rg --location $location --sku B1 --is-linux
az webapp create --name $app --resource-group $rg --plan $plan --runtime "PYTHON:3.11"
az webapp config appsettings set --resource-group $rg --name $app --settings "AZURE_AI_PROJECT_ENDPOINT=https://msftfoundry202912.services.ai.azure.com/api/projects/AI-project1" "AZURE_AI_AGENT_NAME=luna-agent" "SCM_DO_BUILD_DURING_DEPLOYMENT=true"
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated random secret and set it securely:

```powershell
az webapp config appsettings set --resource-group $rg --name $app --settings "FLASK_SECRET_KEY=PASTE_GENERATED_SECRET_HERE"
az webapp config set --resource-group $rg --name $app --startup-file "gunicorn --bind=0.0.0.0:8000 app:app"
az webapp identity assign --resource-group $rg --name $app
```

For a Linux App Service, ensure the startup command is configured as above. The `startup.sh` file is included for reference.

## Grant Foundry access

Grant the App Service's system-assigned managed identity the minimum role required by your Foundry project/agent. For example, an Azure AI User role assignment may be appropriate at the Foundry resource scope, depending on your configuration.

```powershell
$principalId = az webapp identity show --resource-group $rg --name $app --query principalId -o tsv
$foundryRg = "YOUR_FOUNDRY_RESOURCE_GROUP"
$foundryName = "msftfoundry202912"
$foundryId = az cognitiveservices account show --name $foundryName --resource-group $foundryRg --query id -o tsv
az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role "Azure AI User" --scope $foundryId
```

Confirm the correct Foundry resource name, resource group, and permissions in your Azure environment. Allow time for RBAC propagation.

## Configure GitHub secrets

In GitHub, open **Settings → Secrets and variables → Actions** and add:

- `AZURE_WEBAPP_NAME`: your App Service name
- `AZURE_WEBAPP_PUBLISH_PROFILE`: the full publish profile downloaded from the App Service Overview page

Treat the publish profile as a password. Never commit it to the repository. For stricter production setups, consider replacing publish-profile deployment with GitHub OIDC.

## Deploy

Push a commit to `main`. In GitHub, open the **Actions** tab and inspect the `Deploy Luna Agent to Azure App Service` workflow.

After deployment, test:

- `https://YOUR-UNIQUE-LUNA-APP-NAME.azurewebsites.net/health`
- `https://YOUR-UNIQUE-LUNA-APP-NAME.azurewebsites.net/`

## Authentication notes

The app uses `DefaultAzureCredential`. Locally, run `az login` with an identity that has the required Foundry access. In App Service, the system-assigned managed identity is used.

If agent calls fail, check App Service Log stream, endpoint and agent name, managed identity permissions, and whether your project/agent API supports the preview options used by the sample.

## Important security note

This sample does not include per-user authentication or CSRF protection. Before exposing it publicly for production use, add appropriate user authentication, request protections, rate limiting, and monitoring.
