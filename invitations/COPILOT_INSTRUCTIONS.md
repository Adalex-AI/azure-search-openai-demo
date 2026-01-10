# Instructions for Adding New Users to Civil Procedure Copilot

This document provides complete instructions for granting security access to new users of the Civil Procedure Copilot application. It is designed so anyone unfamiliar with the setup can understand and execute the process.

---

## 📋 Overview

**What this process does:**
1. Invites an external user as a **Guest** in the Azure Entra ID tenant
2. Adds them to the **Civil Procedure Copilot Users** security group
3. Creates an email draft with their unique redeem link

**Why we use this approach:**
- ✅ **Azure Best Practice**: Uses Security Groups for scalable access management ([Microsoft recommendation](https://learn.microsoft.com/en-us/entra/identity/conditional-access/plan-conditional-access#minimize-the-number-of-conditional-access-policies))
- ✅ **Principle of Least Privilege**: Users only gain access to this specific application
- ✅ **B2B Collaboration**: Standard Microsoft Entra External ID pattern for guest users
- ✅ **Auditable**: All access is tracked via group membership

---

## 🔐 Security Architecture

### Tenant Information
| Property | Value |
|----------|-------|
| **Tenant ID** | `3bfe16b2-5fcc-4565-b1f1-15271d20fecf` |
| **Tenant Name** | `hbalapatabendigmail.onmicrosoft.com` |
| **Admin Account** | `hbalapatabendi@gmail.com` |

### Application Details
| Property | Value |
|----------|-------|
| **Application Name** | Civil Procedure Copilot |
| **Application URL** | https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io |
| **Server App ID** | `0e5b8dce-464a-42f8-aa39-1044341cf90b` |
| **Client App ID** | `1d382868-51d6-4200-a4ba-3a7b94ecb2d3` |

### Security Group
| Property | Value |
|----------|-------|
| **Group Name** | `Civil Procedure Copilot Users` |
| **Group Object ID** | `36094ff3-5c6d-49ef-b385-fa37118527e3` |
| **Group Type** | Security (not Microsoft 365) |
| **Purpose** | Controls access to the application and documents |

### Document Access Configuration
| Setting | Value | Meaning |
|---------|-------|---------|
| `AZURE_USE_AUTHENTICATION` | `true` | Users must sign in |
| `AZURE_ENFORCE_ACCESS_CONTROL` | `true` | Document-level ACLs are enforced |
| `AZURE_ENABLE_UNAUTHENTICATED_ACCESS` | `true` | Users can browse the UI without login (but cannot search) |

**Current Document ACL Strategy**: All documents in the search index have the security group (`36094ff3-5c6d-49ef-b385-fa37118527e3`) assigned to their `groups` field. Any member of the group automatically has access to all documents.

---

## 👥 Current Authorized Users

As of January 2026, the following users are members of the security group:

| Name | Email | Status | 
|------|-------|--------|
| Matthew Pimley | matthewpimley1@gmail.com | Active |
| C Wright | cwright@st-philips.com | Active |
| Mark Wing | mark.wing@talk21.com | Active |
| Conor Johnston | conor.johnston@outlook.com | Active |
| Kung Kincheung | kung.kincheung@gmail.com | Active |

**To get the current list**, run:
```bash
az ad group member list --group "Civil Procedure Copilot Users" --query "[].{Name:displayName, Email:mail}" -o table
```

---

## 🚀 Phase 1: Grant Security Access (Azure CLI)

### Prerequisites
- Azure CLI installed and logged in (`az login`)
- Sufficient permissions (Guest Inviter role or User Administrator)

### Step 1: Invite the User

Run the following command to invite the user as a guest. This uses the Microsoft Graph API.

```bash
az rest --method post --url https://graph.microsoft.com/v1.0/invitations \
  --body '{
    "invitedUserEmailAddress": "<USER_EMAIL>",
    "inviteRedirectUrl": "https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io",
    "sendInvitationMessage": true,
    "invitedUserDisplayName": "<USER_DISPLAY_NAME>"
  }'
```

**Replace:**
- `<USER_EMAIL>` with the user's email address
- `<USER_DISPLAY_NAME>` with their full name

**Example:**
```bash
az rest --method post --url https://graph.microsoft.com/v1.0/invitations \
  --body '{
    "invitedUserEmailAddress": "john.smith@example.com",
    "inviteRedirectUrl": "https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io",
    "sendInvitationMessage": true,
    "invitedUserDisplayName": "John Smith"
  }'
```

### Step 2: Extract Critical Information from Output

The command returns JSON output. **Save these two values:**

1. **Redeem URL** (`inviteRedeemUrl`): The link the user clicks to accept the invitation
2. **User Object ID** (`invitedUser.id`): The unique ID needed to add them to the group

**Example output:**
```json
{
  "inviteRedeemUrl": "https://login.microsoftonline.com/redeem?rd=...",
  "invitedUser": {
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

### Step 3: Add User to Security Group

Add the user to the security group using their Object ID:

```bash
az ad group member add --group "Civil Procedure Copilot Users" --member-id <USER_OBJECT_ID>
```

**Example:**
```bash
az ad group member add --group "Civil Procedure Copilot Users" --member-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 📧 Phase 2: Create Invitation Email Draft

Create a text file in the `invitations/` folder for record-keeping and to provide the email content.

### Step 1: Create Individual File

Create a new file named `firstname_lastname.txt` (lowercase, snake_case):

**Content Template:**
```text
Subject: Access to Civil Procedure Copilot

Email: <USER_EMAIL>
Redeem link:
<PASTE_REDEEM_URL_FROM_STEP_2>

App URL:
https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io

Instructions:
1) Click the redeem link and accept the invitation
2) Sign in with your Microsoft account
3) Visit the app URL to start searching
```

### Step 2: Update Summary File

Add the new filename to `invitations/email_drafts.txt`:

```text
- firstname_lastname.txt
```

---

## ✅ Phase 3: Verification and Reporting

### Step 1: Verify Group Membership

Run the following to confirm the user was added:

```bash
az ad group member list --group "Civil Procedure Copilot Users" --query "[].{Name:displayName, Email:mail, UserPrincipalName:userPrincipalName}" -o table
```

### Step 2: Confirm with User

- Notify the admin that the user has been added to Entra ID
- Confirm the draft email file is ready in `invitations/`
- **Present the updated list of authorized users**

---

## 🔄 Adding New Documents

All documents in the search index are configured to be accessible ONLY by members of the **Civil Procedure Copilot Users** security group.

**Automatic Access Control:**
The ingestion process has been customized to **automatically assign the security group** (`36094ff3-5c6d-49ef-b385-fa37118527e3`) to all new documents in the Azure AI Search index.

No manual scripts are required after ingestion. The system ensures rigorous group-based access control is applied by default.

*(Note: The `scripts/add_group_to_all_docs.py` script remains available as a backup mechanism if needed).*

---

## 🗑️ Removing User Access

### Remove from Security Group
```bash
az ad group member remove --group "Civil Procedure Copilot Users" --member-id <USER_OBJECT_ID>
```

### Find User Object ID
```bash
az ad user show --id "<USER_EMAIL>" --query id -o tsv
```

### Delete Guest User (Optional)
```bash
az ad user delete --id <USER_OBJECT_ID>
```

---

## 📚 References

- [Azure B2B Quickstart: Add Guest Users](https://learn.microsoft.com/en-us/entra/external-id/b2b-quickstart-add-guest-users-portal)
- [Plan Conditional Access Deployment](https://learn.microsoft.com/en-us/entra/identity/conditional-access/plan-conditional-access)
- [Manage Groups in Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/fundamentals/how-to-manage-groups)
- [Azure Search Document-Level Security](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search)
