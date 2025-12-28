# Sharing the Legal RAG Application with Users

This guide explains how to share the Legal Court RAG application with external users (such as lawyers) while maintaining proper security controls.

## Current Security Configuration

Your application is configured with the following security settings:

| Setting | Value | Description |
|---------|-------|-------------|
| `AZURE_USE_AUTHENTICATION` | `true` | Microsoft Entra ID login is enabled |
| `AZURE_ENFORCE_ACCESS_CONTROL` | `true` | Document-level access control is enforced |
| `AZURE_ENABLE_UNAUTHENTICATED_ACCESS` | `true` | Users can browse without login (but cannot search documents) |

**Application URL:** https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io

---

## Option 1: Add Users to Your Azure AD Tenant (Recommended for Controlled Access)

This is the most secure option for sharing with specific lawyers in your organization.

### Step 1: Add the User as a Guest in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** → **Users**
3. Click **+ New user** → **Invite external user**
4. Enter the lawyer's email address
5. Add a personal message explaining access to the Legal RAG system
6. Click **Invite**

The user will receive an email invitation to join your tenant.

### Step 2: Grant API Permissions (If Required)

If users see "Consent Required" errors:

1. Navigate to **Microsoft Entra ID** → **Enterprise applications**
2. Find your Client App: `Azure Search OpenAI Chat Web App` (ID: `1d382868-51d6-4200-a4ba-3a7b94ecb2d3`)
3. Go to **Permissions** → **Grant admin consent**

### Step 3: Assign Document Access (Optional)

If you want to restrict which documents the user can see:

```bash
# Activate Python environment
source .venv/bin/activate

# Add user's Object ID to specific documents
python ./scripts/manageacl.py -v --acl-type oids --acl-action add \
  --acl <USER-OBJECT-ID> \
  --url https://<storage-account>.blob.core.windows.net/content/document.pdf
```

To find a user's Object ID:
1. Go to **Microsoft Entra ID** → **Users**
2. Click on the user
3. Copy the **Object ID** from the Overview page

---

## Option 2: Create a Security Group for Lawyers

Better for managing multiple users with the same access level.

### Step 1: Create a Security Group

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** → **Groups**
3. Click **+ New group**
   - Group type: **Security**
   - Group name: `Legal RAG Users` (or similar)
   - Membership type: **Assigned**
4. Click **Create**

### Step 2: Add Members to the Group

1. Open the group you created
2. Go to **Members** → **+ Add members**
3. Search for and select the users to add
4. Click **Select**

### Step 3: Grant Group Access to Documents

```bash
# Add the group's Object ID to documents
python ./scripts/manageacl.py -v --acl-type groups --acl-action add \
  --acl <GROUP-OBJECT-ID> \
  --url https://<storage-account>.blob.core.windows.net/content/document.pdf
```

---

## Option 3: Enable Global Document Access (Least Restrictive)

If you want all authenticated users to access all documents:

### Enable Global Access on All Documents

```bash
# This grants access to all signed-in users for documents without specific ACLs
python ./scripts/manageacl.py --acl-action enable_global_access
```

This sets the special `["all"]` value on documents, making them available to any authenticated user.

---

## User Experience Flow

### What Users Will See

1. **First Visit:** User navigates to the application URL
2. **Login Prompt:** User clicks "Login" button in the top-right corner
3. **Microsoft Sign-In:** User signs in with their Microsoft account
4. **Consent Screen:** First-time users may see a consent dialog asking for permissions:
   - "Access Azure Search OpenAI Chat API"
   - "Read your profile"
5. **Access Granted:** User can now use the chat interface to query legal documents

### If Users Cannot Login

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| "Admin approval required" | Tenant admin needs to grant consent for the app |
| "User not found" | Invite the user as a guest to your tenant |
| "No access to documents" | Add user/group to document ACLs or enable global access |
| "AADSTS65001 consent error" | Grant admin consent in Enterprise Applications |

---

## Quick Reference: Azure Portal URLs

| Task | URL |
|------|-----|
| Manage Users | https://portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserManagementMenuBlade/~/AllUsers |
| Manage Groups | https://portal.azure.com/#view/Microsoft_AAD_IAM/GroupsManagementMenuBlade/~/AllGroups |
| Enterprise Apps | https://portal.azure.com/#view/Microsoft_AAD_IAM/StartboardApplicationsMenuBlade/~/AppAppsPreview |
| App Registrations | https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps |

---

## Security Best Practices

1. **Use Groups, Not Individual Permissions** - Easier to manage at scale
2. **Review Access Regularly** - Audit who has access to the application
3. **Use Document-Level ACLs** - Restrict sensitive documents to specific users/groups
4. **Monitor Sign-In Logs** - Check Azure AD sign-in logs for unusual activity
5. **Rotate App Secrets** - Periodically rotate `AZURE_SERVER_APP_SECRET` and `AZURE_CLIENT_APP_SECRET`

---

## Revoking Access

### Remove a Specific User

1. Go to **Microsoft Entra ID** → **Enterprise applications**
2. Select `Azure Search OpenAI Chat Web App`
3. Go to **Users and groups**
4. Remove the user from the list

### Remove a User from a Group

1. Go to **Microsoft Entra ID** → **Groups**
2. Select the group
3. Go to **Members** → Remove the user

### Remove Document Access

```bash
# Remove specific user's access to a document
python ./scripts/manageacl.py -v --acl-type oids --acl-action remove \
  --acl <USER-OBJECT-ID> \
  --url https://<storage-account>.blob.core.windows.net/content/document.pdf

# Remove all user access to a document
python ./scripts/manageacl.py -v --acl-type oids --acl-action remove_all \
  --url https://<storage-account>.blob.core.windows.net/content/document.pdf
```

---

## Appendix: Environment Variable Reference

| Variable | Current Value | Description |
|----------|---------------|-------------|
| `AZURE_AUTH_TENANT_ID` | `3bfe16b2-5fcc-4565-b1f1-15271d20fecf` | Azure AD Tenant for authentication |
| `AZURE_SERVER_APP_ID` | `0e5b8dce-464a-42f8-aa39-1044341cf90b` | Server API app registration |
| `AZURE_CLIENT_APP_ID` | `1d382868-51d6-4200-a4ba-3a7b94ecb2d3` | Client UI app registration |
| `AZURE_USE_AUTHENTICATION` | `true` | Authentication enabled |
| `AZURE_ENFORCE_ACCESS_CONTROL` | `true` | Document ACLs enforced |
| `AZURE_ENABLE_UNAUTHENTICATED_ACCESS` | `true` | Allows browsing without login |

---

## Related Documentation

- [Microsoft Entra ID Guest Access](https://learn.microsoft.com/entra/external-id/what-is-b2b)
- [Managing Groups in Azure AD](https://learn.microsoft.com/entra/fundamentals/how-to-manage-groups)
- [Azure AI Search Document-Level Security](https://learn.microsoft.com/azure/search/search-security-trimming-for-azure-search)
