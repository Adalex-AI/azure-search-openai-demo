# Data Privacy & Security Guide for Civil Procedure Copilot

**Version:** 1.0
**Last Updated:** December 2024
**Audience:** Lawyers and legal professionals using the Civil Procedure Copilot

***

## Executive Summary

This Civil Procedure Copilot uses **Microsoft Azure OpenAI Service** to provide AI-powered search and question-answering capabilities for Civil Procedure Rules (CPR), Practice Directions, and Court Guides applicable to England and Wales.

### Key Takeaways

| ✅ What We Guarantee | ❌ What Does NOT Happen |
|---------------------|------------------------|
| Your data stays within Azure | Your CPR queries are NOT used to train AI models |
| Enterprise-grade encryption | Your data is NOT shared with OpenAI (ChatGPT) |
| Access control & authentication | Your data is NOT available to other customers |
| Stateless AI processing | The AI does NOT remember your previous queries |

***

## 1. What This Application Searches

This Civil Procedure Copilot indexes the following publicly available legal documents:

| Document | Edition/Version |
|----------|-----------------|
| **Civil Procedure Rules (CPR)** | Parts 1-89 with associated Practice Directions |
| **Commercial Court Guide** | 11th Edition, July 2023 |
| **King's Bench Division Guide** | 2025 Edition |
| **Chancery Guide** | 2022 |
| **Patents Court Guide** | February 2025 |
| **Technology and Construction Court Guide** | October 2022 |
| **Circuit Commercial Court Guide** | August 2023 |

These are all publicly available court documents. The AI uses these indexed sources to answer your questions about procedural rules, court practices, and litigation procedures.

***

## 2. How Your Query is Processed

When you ask a question about CPR or court procedures:

1. **Your question** is sent to our Azure-hosted backend
1. **Azure AI Search** retrieves the most relevant CPR sections, Practice Directions, or Court Guide passages
1. **Azure OpenAI** generates an answer based **only** on the retrieved legal documents
1. **Citations** are provided so you can verify the source
1. **The AI forgets** your query immediately—it's stateless (no memory of previous sessions)

```text
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐
│  Your CPR Question  │ ──▶ │  Azure AI Search     │ ──▶ │  Azure OpenAI            │
│                     │     │  (CPR, Court Guides) │     │  (Generates answer from  │
└─────────────────────┘     └──────────────────────┘     │  retrieved documents)    │
                                      │                  └──────────────────────────┘
                                      │                             │
                                      ◀────────── Answer + Citations ┘
```

**Important:** The AI can only answer based on the indexed documents. It does not have access to external legal databases, your firm's documents, or real-time court information.

***

## 3. Microsoft Azure OpenAI Data Commitments

Microsoft makes the following contractual commitments for Azure OpenAI:

### 3.1 Your Data is NOT Used for Training

> *"Your prompts (inputs) and completions (outputs), your embeddings, and your training data are NOT used to train any generative AI foundation models without your permission or instruction."*
>
> — Microsoft Azure OpenAI Documentation

This means:

- Your legal queries never become part of the AI's training data
- Asking about specific cases, clients, or legal matters is protected
- Microsoft cannot learn from your usage patterns

### 3.2 Your Data is NOT Shared

> *"Your prompts and completions are NOT available to other customers, NOT available to OpenAI, and NOT used to improve Microsoft or third-party products or services without your explicit permission."*

This means:

- Other Azure customers cannot access your queries
- OpenAI (the company) never sees your data
- ChatGPT users cannot access your legal research

### 3.3 Azure OpenAI vs ChatGPT

| Aspect | Azure OpenAI (What We Use) | ChatGPT (What We DON'T Use) |
|--------|---------------------------|----------------------------|
| Data isolation | ✅ Enterprise isolation | ❌ Shared platform |
| Training on your data | ✅ Never | ⚠️ May be used unless opted out |
| Compliance | ✅ SOC 2, ISO 27001, GDPR | Variable |
| Data residency | ✅ Configurable | ❌ OpenAI servers |

***

## 4. What Data is Stored

### 4.1 Data That IS Stored

| Data Type | Where Stored | Who Controls It | Retention |
|-----------|--------------|-----------------|-----------|
| Legal documents (CPR, etc.) | Azure AI Search & Blob Storage | Our organization | Permanent (our policy) |
| Chat history (if enabled) | Azure Cosmos DB | Our organization | User-deletable |
| User authentication tokens | Azure AD | Microsoft & our organization | Session-based |

### 4.2 Data That is NOT Stored

| Data Type | Why It's Not Stored |
|-----------|---------------------|
| AI model's "memory" of your queries | Models are stateless—they don't remember previous queries |
| Your prompts in OpenAI systems | Azure OpenAI doesn't retain prompts after processing |
| Training data derived from your usage | Microsoft contractually prohibits this |

***

## 5. Content Safety & Abuse Monitoring

Azure OpenAI includes content safety measures to prevent misuse. Here's how it works:

### 5.1 Real-Time Content Filtering

- AI classifiers check prompts and responses for harmful content
- Filtering happens automatically and instantly
- No data is stored as part of this filtering

### 5.2 Abuse Monitoring

To prevent misuse of Azure OpenAI, Microsoft implements abuse monitoring:

**Default Behavior (Automated Review):**

- If content is flagged, AI models may review it to detect abuse patterns
- Prompts reviewed this way are **NOT stored**
- No human sees your data under normal circumstances

**Human Review (Exceptional Cases):**

- Only occurs if automated systems detect potential severe abuse
- Authorized Microsoft employees may review flagged content
- Access requires Secure Access Workstations (SAWs) and Just-In-Time approval
- For EU deployments, reviewers are located in the EU

### 5.3 Modified Abuse Monitoring (Enterprise Option)

Organizations handling highly sensitive data can apply to Microsoft for modified abuse monitoring, which eliminates human review. This may be appropriate for:

- Attorney-client privileged communications
- Sensitive litigation matters
- Confidential transaction details

Contact your IT administrator if this is a concern.

***

## 6. Data Residency

### 6.1 Where Data is Processed

- **Azure Region:** Data is processed in the Azure region where the service is deployed
- **Within Microsoft Infrastructure:** All processing occurs within Microsoft's Azure data centers
- **Encryption in Transit:** TLS 1.2 or higher for all communications

### 6.2 Data Residency Options

| Deployment Type | Data Processing Location |
|-----------------|-------------------------|
| Standard | Within the deployed Azure region |
| Data Zone | Within the specified data zone (e.g., EU) |
| Global | May be processed in any region with the model |

***

## 7. Compliance & Certifications

Azure OpenAI Service inherits Azure's compliance certifications:

| Certification | Description |
|---------------|-------------|
| SOC 2 Type II | Security, availability, and confidentiality controls |
| ISO 27001 | Information security management |
| GDPR | EU data protection compliance |
| HIPAA | Healthcare data protection (if configured) |
| UK G-Cloud | UK government cloud certification |

***

## 8. Best Practices for Lawyers Using the CPR Research Assistant

### 8.1 What You CAN Safely Do

✅ Ask questions about CPR rules, Parts, and Practice Directions
✅ Research court procedures for Commercial Court, King's Bench, Chancery Division, etc.
✅ Query time limits for claims, statements of case, and appeals
✅ Explore case management requirements and pre-action protocols
✅ Research service requirements and court fee rules
✅ Ask about disclosure, witness evidence, and trial procedures
✅ Query specific court requirements (e.g., Commercial Court skeleton argument rules)

### 8.2 Example Safe Queries

- "What are the time limits for filing an Acknowledgement of Service?"
- "What does CPR Part 36 say about settlement offers?"
- "What are the requirements for a witness statement under CPR Part 32?"
- "What does the Commercial Court Guide say about case management conferences?"
- "What are the requirements for issuing proceedings in the Technology and Construction Court?"

### 8.3 Recommendations

⚠️ **Avoid including real client names** in queries when possible
⚠️ **Use generic placeholders** for specific case details (e.g., "Claimant" vs actual name)
⚠️ **Clear chat history** after sessions if preferred
⚠️ **Verify AI answers** against the source CPR or Court Guide citations provided
⚠️ **Check Practice Direction dates** - procedures may have been updated

### 8.4 What to Remember

- AI responses are **assistive, not authoritative**—always verify against source materials
- The system indexes specific Court Guide editions (see Section 1)—procedures may have been updated
- Always confirm current court fees and deadlines via official court channels
- Check with your supervising solicitor about firm policies on AI use
- The AI may make mistakes—professional judgment is essential

***

## 9. Frequently Asked Questions

### Q: Does OpenAI (the company) see my queries?

**No.** Azure OpenAI is a separate service hosted entirely within Microsoft Azure. Your data never goes to OpenAI's systems.

### Q: Will my questions be used to improve ChatGPT?

**No.** Azure OpenAI does not share data with OpenAI's consumer products. Your queries are never used to train any models.

### Q: Can other lawyers using this system see my queries?

**No.** Each user's queries are isolated. There is no shared query history between users.

### Q: How long are my queries retained?

The AI models themselves don't retain queries at all—they're stateless. Chat history (if enabled) is stored in our organization's database and can be cleared by users.

### Q: Are the CPR and Court Guides in this system up to date?

The system indexes specific document versions (see Section 1). Always verify critical deadlines and procedures via the official judiciary website or Rules Committee updates, as CPR amendments occur regularly.

### Q: Can I rely on this for urgent deadline calculations?

Use this for research and guidance, but always verify critical deadlines (limitation periods, filing dates, etc.) via official court sources. The AI may not reflect the most recent CPR amendments.

### Q: Is this system appropriate for privileged communications?

This system is designed for legal research on CPR and court procedures using publicly available documents. The queries themselves are not retained. For highly sensitive matters, consult your firm's technology and ethics guidance.

### Q: What happens if I accidentally include client details?

The data is not used for training and is not shared with other users or OpenAI. However, as a matter of good practice, we recommend using generic placeholders where possible.

### Q: Where can I find the source document for a citation?

The AI provides source citations (e.g., "CPR Part 24", "Commercial Court Guide §3.2"). You can find the official documents at:

- **CPR & Practice Directions:** [justice.gov.uk](https://www.justice.gov.uk/courts/procedure-rules/civil)
- **Commercial Court Guide:** [judiciary.uk](https://www.judiciary.uk/guidance-and-resources/commercial-court-guide/)
- **Other Court Guides:** Check the relevant court's page on judiciary.uk

***

## 10. Official Microsoft Documentation

For authoritative and up-to-date information:

- **Data, Privacy, and Security:** https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/data-privacy
- **Abuse Monitoring:** https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/abuse-monitoring
- **Content Filtering:** https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter
- **Microsoft Trust Center:** https://www.microsoft.com/trust-center

***

## 11. Contact & Support

If you have questions about data privacy or security:

- **Technical Issues:** Contact your IT administrator
- **Privacy Concerns:** Contact your organization's Data Protection Officer
- **Usage Questions:** Refer to the application help or contact the system administrator

***

*This document is provided for informational purposes. For binding legal commitments, refer to your organization's Microsoft Enterprise Agreement and Azure service terms.*
