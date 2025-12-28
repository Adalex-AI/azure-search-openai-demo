# Email Template: Inviting Lawyers to the Legal RAG System

---

## Data Privacy & Security Information for Lawyers

**Important:** This section provides key information about how your data is handled when using this Legal RAG application. Please share this with all users.

### 🔒 Key Data Protection Assurances

This application uses **Azure OpenAI Service**, Microsoft's enterprise AI platform. Here are the critical privacy assurances from Microsoft:

| Assurance | Details |
|-----------|---------|
| ✅ **NOT used for AI training** | Your prompts (questions) and responses are NOT used to train, retrain, or improve Azure OpenAI's foundation models |
| ✅ **NOT shared with other customers** | Your data is completely isolated and never available to other Azure customers |
| ✅ **NOT shared with OpenAI** | Azure OpenAI operates independently from OpenAI's public services (ChatGPT, OpenAI API). Your data never goes to OpenAI |
| ✅ **Stateless processing** | The AI models do not store your prompts or responses—they are stateless |
| ✅ **Enterprise-grade security** | All data is encrypted in transit (TLS 1.2+) and at rest |

### 📊 How Your Data is Handled

**During a query:**
- Your question is sent to Azure OpenAI for processing
- The model generates a response which is returned to you
- The model itself does NOT retain your query or the response
- No human at Microsoft sees your queries under normal operation

**Chat history (if enabled):**
- Conversations may be stored in our Azure database to allow session continuity
- This data is stored in our Azure tenant, NOT by OpenAI
- Chat history can be deleted by users

**Document content:**
- Legal documents are stored in Azure AI Search and Azure Blob Storage
- All data remains within our Azure subscription with appropriate access controls
- Documents are not exposed to OpenAI or other customers

### 🛡️ Content Safety & Abuse Monitoring

Azure OpenAI includes content safety measures:

1. **Automated filtering**: AI models filter potentially harmful content in real-time
2. **Automated review**: If content is flagged, AI systems may review it to detect abuse patterns—prompts reviewed this way are NOT stored
3. **Human review (rare)**: In exceptional cases of suspected severe abuse, authorized Microsoft employees may review flagged content using secure access controls
4. **Enterprise option**: Organizations processing highly sensitive data can apply to Microsoft to modify or disable abuse monitoring with human review

### 📍 Data Residency

- Data is processed within Microsoft's Azure infrastructure
- Processing location depends on the Azure OpenAI deployment region
- All data transmission is encrypted

### ⏱️ Data Retention

| Data Type | Retention |
|-----------|-----------|
| Model processing | NOT retained—models are stateless |
| Chat history (if enabled) | Per our organization's policy; user-deletable |
| Abuse monitoring (if flagged) | Up to 30 days if human review occurs |

### 📚 Official Microsoft Documentation

For authoritative information, please refer to:
- [Azure OpenAI Data, Privacy, and Security](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/data-privacy)
- [Azure OpenAI Abuse Monitoring](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/abuse-monitoring)
- [Microsoft Trust Center](https://www.microsoft.com/trust-center)

---

## Email Option 1: Internal Organization Users

**Subject:** Access to Legal Document Research Assistant - AI-Powered CPR Search Tool

---

Dear [Lawyer's Name],

I'm pleased to invite you to use our new **Legal Document Research Assistant** – an AI-powered tool that allows you to quickly search and query our legal document database, including Civil Procedure Rules (CPR) and related materials.

### What is this tool?

This is a secure, internal application that uses Azure OpenAI and Azure AI Search to help you:
- **Ask questions in plain English** about legal procedures, court rules, and compliance requirements
- **Get instant answers** with citations to the source documents
- **Access relevant passages** from our legal document library

### How to Access

1. **Click this link:** [https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io](https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io)

2. **Click "Login"** in the top-right corner

3. **Sign in with your Microsoft account** (work email address)

4. **Approve the permissions** when prompted (first time only)

5. **Start asking questions!** For example:
   - "What are the time limits for filing a defence?"
   - "Explain the pre-action protocol requirements"
   - "What is the overriding objective in CPR Part 1?"

### Security & Privacy

This application is:
- ✅ **Authenticated** – Only authorized users with valid Microsoft accounts can access it
- ✅ **Encrypted** – All data is transmitted over HTTPS
- ✅ **Access-Controlled** – Document access is restricted based on your permissions
- ✅ **Azure-Hosted** – Runs entirely within Microsoft Azure's secure cloud environment
- ✅ **No AI Training** – Your queries are NOT used to train AI models
- ✅ **Data Isolation** – Your data is never shared with other customers or OpenAI

**📋 Full Data Privacy Information:** See the "Data Privacy & Security Information for Lawyers" section at the top of this document for comprehensive details about how your data is handled.

### Getting Help

If you encounter any issues logging in or using the application, please contact me and I'll assist you.

I look forward to your feedback on this tool!

Best regards,

[Your Name]  
[Your Title]  
[Your Contact Information]

---

## Email Option 2: External Guest Users (Lawyers Outside Your Organization)

**Subject:** Invitation: Access Legal Document Research Tool – AI-Powered CPR Assistant

---

Dear [Lawyer's Name],

You've been invited to access our **Legal Document Research Assistant**, an AI-powered tool for searching Civil Procedure Rules and legal documentation.

### Accepting Your Invitation

You should have received a separate invitation email from Microsoft Azure with the subject line: **"[Organization] invited you to access applications within their organization"**

Please:
1. **Check your inbox** (and spam folder) for this Microsoft invitation
2. **Click "Accept invitation"** in that email
3. **Sign in** with your work or personal Microsoft account
4. **Complete the consent process**

If you haven't received the invitation, please let me know and I'll resend it.

### Accessing the Application

Once you've accepted the invitation:

1. **Navigate to:** [https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io](https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io)

2. **Click "Login"** and sign in with the account you used to accept the invitation

3. **Approve permissions** when prompted (first-time only)

### What You Can Do

The Legal RAG Assistant allows you to:
- Ask natural language questions about legal procedures
- Search across our curated legal document library
- Receive AI-generated answers with source citations
- Access relevant passages and supporting documentation

### Example Questions

Try asking:
- "What are the requirements for service of documents under CPR Part 6?"
- "Explain the small claims track allocation criteria"
- "What are the grounds for setting aside a default judgment?"

### Security Information

- **Authentication:** Microsoft Entra ID (Azure Active Directory)
- **Access Control:** Document-level permissions ensure you only see authorized content
- **Data Protection:** All communications are encrypted (HTTPS/TLS)
- **Hosting:** Microsoft Azure (UK data residency available)

### Need Help?

If you have any trouble:
- **Cannot accept invitation:** Ensure you're using a valid Microsoft account (work, school, or personal)
- **Login errors:** Try using a private/incognito browser window
- **Permission denied:** Contact me to verify your access rights

Please don't hesitate to reach out if you have any questions.

Kind regards,

[Your Name]  
[Your Title]  
[Your Organization]  
[Your Email]  
[Your Phone]

---

## Email Option 3: Brief Internal Announcement

**Subject:** New Tool Available: AI Legal Document Assistant

---

Hi Team,

We've launched a new **AI-powered Legal Document Assistant** for searching our CPR and legal procedure documentation.

**Access it here:** [https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io](https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io)

**How it works:**
1. Login with your work Microsoft account
2. Type a question in plain English
3. Get an AI-generated answer with source citations

**Example questions to try:**
- "What is the overriding objective?"
- "Time limits for appealing a court order?"
- "Pre-action protocol for personal injury claims"

This is a secure, authenticated application hosted on Azure. Let me know if you have any questions or feedback!

[Your Name]

---

## Quick Checklist for Administrator

Before sending invitations, ensure:

- [ ] User is added as a guest in Azure AD (for external users)
- [ ] User has been added to appropriate security groups (if using group-based access)
- [ ] Document ACLs are configured correctly
- [ ] Admin consent has been granted for the application
- [ ] Test login works with a test account

### Azure Portal Quick Links

| Task | Action |
|------|--------|
| Invite Guest User | [Azure Portal → Users → New User → Invite External](https://portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserManagementMenuBlade/~/AllUsers) |
| Create Security Group | [Azure Portal → Groups → New Group](https://portal.azure.com/#view/Microsoft_AAD_IAM/GroupsManagementMenuBlade/~/AllGroups) |
| Grant Admin Consent | [Azure Portal → Enterprise Apps → Your App → Permissions](https://portal.azure.com/#view/Microsoft_AAD_IAM/StartboardApplicationsMenuBlade/~/AppAppsPreview) |
