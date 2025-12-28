// Data Privacy Notice Component
// ==============================
// Displays important data privacy and security information to users
// about Azure OpenAI data handling policies for the Legal CPR Research Assistant.

import React, { useState } from "react";
import { Panel, PanelType, IconButton, Text, Stack, MessageBar, MessageBarType, Link, Icon } from "@fluentui/react";

import styles from "./DataPrivacyNotice.module.css";

interface DataPrivacyNoticeProps {
    /** If true, shows a small banner at the bottom of the screen */
    showBanner?: boolean;
}

export const DataPrivacyNotice: React.FC<DataPrivacyNoticeProps> = ({ showBanner = true }) => {
    const [isPanelOpen, setIsPanelOpen] = useState(false);
    const [bannerDismissed, setBannerDismissed] = useState(() => {
        return sessionStorage.getItem("privacyBannerDismissed") === "true";
    });

    const openPanel = () => setIsPanelOpen(true);
    const dismissPanel = () => setIsPanelOpen(false);

    const dismissBanner = () => {
        setBannerDismissed(true);
        sessionStorage.setItem("privacyBannerDismissed", "true");
    };

    return (
        <>
            {/* Privacy Banner */}
            {showBanner && !bannerDismissed && (
                <div className={styles.privacyBanner}>
                    <MessageBar
                        messageBarType={MessageBarType.info}
                        isMultiline={false}
                        onDismiss={dismissBanner}
                        dismissButtonAriaLabel="Close"
                        actions={
                            <div>
                                <Link onClick={openPanel}>Learn more</Link>
                            </div>
                        }
                    >
                        <Icon iconName="Shield" style={{ marginRight: 8 }} />
                        <strong>Data Privacy:</strong> Your CPR queries are not used to train AI models and are not shared with OpenAI or other customers.
                    </MessageBar>
                </div>
            )}

            {/* Privacy Info Button (always accessible) */}
            <IconButton
                iconProps={{ iconName: "Shield" }}
                title="Data Privacy & Security"
                ariaLabel="Data Privacy & Security Information"
                onClick={openPanel}
                className={styles.privacyButton}
            />

            {/* Privacy Panel */}
            <Panel
                isOpen={isPanelOpen}
                onDismiss={dismissPanel}
                type={PanelType.medium}
                headerText="Legal CPR Assistant: Data Privacy & Security"
                closeButtonAriaLabel="Close"
            >
                <Stack tokens={{ childrenGap: 20 }} className={styles.panelContent}>
                    {/* About This System */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="Gavel" className={styles.sectionIcon} />
                            About This Legal Research Tool
                        </Text>
                        <Text block>
                            This application helps lawyers and legal professionals search and query the <strong>Civil Procedure Rules (CPR)</strong>, Practice
                            Directions, and Court Guides for England and Wales using AI-powered search.
                        </Text>
                        <Stack tokens={{ childrenGap: 4 }} style={{ marginTop: 8 }}>
                            <Text block>
                                <strong>Document sources indexed:</strong>
                            </Text>
                            <Text block>• Civil Procedure Rules (Parts 1-89) and Practice Directions</Text>
                            <Text block>• Commercial Court Guide (11th Edition, July 2023)</Text>
                            <Text block>• King's Bench Division Guide (2025 Edition)</Text>
                            <Text block>• Chancery Guide (2022)</Text>
                            <Text block>• Patents Court Guide (February 2025)</Text>
                            <Text block>• Technology and Construction Court Guide (October 2022)</Text>
                            <Text block>• Circuit Commercial Court Guide (August 2023)</Text>
                        </Stack>
                    </section>

                    {/* Key Assurances Section */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="ShieldSolid" className={styles.sectionIcon} />
                            Key Data Protection Assurances
                        </Text>
                        <Stack tokens={{ childrenGap: 12 }} className={styles.assuranceList}>
                            <div className={styles.assuranceItem}>
                                <Icon iconName="CheckMark" className={styles.checkIcon} />
                                <Text>
                                    <strong>Your queries are NOT used for AI training:</strong> Questions you ask about CPR, Practice Directions, or Court
                                    procedures are NOT used to train, retrain, or improve any AI models. Microsoft contractually prohibits this.
                                </Text>
                            </div>
                            <div className={styles.assuranceItem}>
                                <Icon iconName="CheckMark" className={styles.checkIcon} />
                                <Text>
                                    <strong>NOT shared with anyone:</strong> Your queries are processed only within your session. Other testers, other Azure
                                    customers, and third parties cannot access your queries. No chat history is retained after your session.
                                </Text>
                            </div>
                            <div className={styles.assuranceItem}>
                                <Icon iconName="CheckMark" className={styles.checkIcon} />
                                <Text>
                                    <strong>NOT sent to OpenAI (ChatGPT):</strong> This uses <strong>Azure OpenAI</strong>, which is a separate enterprise
                                    service hosted entirely within Microsoft Azure. Your queries never go to OpenAI's public ChatGPT or OpenAI API services.
                                </Text>
                            </div>
                            <div className={styles.assuranceItem}>
                                <Icon iconName="CheckMark" className={styles.checkIcon} />
                                <Text>
                                    <strong>AI models are stateless:</strong> The GPT model does not "remember" your previous questions. Each query is processed
                                    independently with no persistent memory in the model itself.
                                </Text>
                            </div>
                        </Stack>
                    </section>

                    {/* How It Works Section */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="Workflow" className={styles.sectionIcon} />
                            How Your Query is Processed
                        </Text>
                        <Stack tokens={{ childrenGap: 8 }}>
                            <Text block>
                                <strong>1. You ask a question</strong> about CPR rules, court procedures, or practice directions.
                            </Text>
                            <Text block>
                                <strong>2. Azure AI Search retrieves relevant passages</strong> from the indexed legal documents (CPR, Court Guides, etc.)
                                stored in Azure.
                            </Text>
                            <Text block>
                                <strong>3. Azure OpenAI generates a response</strong> based on the retrieved passages. The model (GPT-5-nano) processes your
                                query and the context, then returns an answer with citations.
                            </Text>
                            <Text block>
                                <strong>4. The model immediately forgets</strong> your query after processing—it is stateless and does not retain any memory of
                                your question.
                            </Text>
                        </Stack>
                    </section>

                    {/* What Data is Stored */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="Database" className={styles.sectionIcon} />
                            What Data is Stored
                        </Text>
                        <Stack tokens={{ childrenGap: 8 }}>
                            <Text block>
                                <strong>Legal document content:</strong> The CPR, Practice Directions, and Court Guides are stored in Azure AI Search and Azure
                                Blob Storage. These are publicly available legal documents.
                            </Text>
                            <Text block>
                                <strong>Chat history:</strong> Chat history storage is <strong>not enabled</strong> for this test environment. Your queries are
                                not saved after your browser session ends.
                            </Text>
                            <Text block>
                                <strong>Feedback reports:</strong> If you submit feedback using the thumbs up/down buttons, the following is logged to Azure
                                Application Insights for quality improvement purposes:
                            </Text>
                            <Stack tokens={{ childrenGap: 4 }} style={{ marginLeft: 16 }}>
                                <Text block>• Your rating (helpful/unhelpful)</Text>
                                <Text block>• Issue categories you selected (e.g., "incorrect citation", "outdated law")</Text>
                                <Text block>• Any comments you provide</Text>
                                <Text block>• A message ID (anonymous identifier for the response)</Text>
                                <Text block>
                                    • <strong>Optionally:</strong> If you choose to share your prompt and search details when reporting an issue, your question,
                                    conversation history, and search/thought process data will also be included. You will be shown exactly what will be shared
                                    and must explicitly consent before this data is included.
                                </Text>
                            </Stack>
                            <Text block style={{ fontStyle: "italic" }}>
                                Note: Feedback is voluntary and anonymous. Your name and email are not attached to feedback reports. Sharing your prompt is
                                optional and requires explicit consent.
                            </Text>
                            <Text block>
                                <strong>Authentication:</strong> Your Microsoft Entra ID login session is managed by Azure Active Directory.
                            </Text>
                            <Text block style={{ marginTop: 8, fontStyle: "italic" }}>
                                <strong>Your queries are NOT stored:</strong> The AI model does not store or retain your queries. Your questions are processed
                                and immediately discarded—nothing is saved (unless you choose to share them in a feedback report).
                            </Text>
                        </Stack>
                    </section>

                    {/* Content Safety */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="Info" className={styles.sectionIcon} />
                            Content Safety & Abuse Monitoring
                        </Text>
                        <Text block>
                            Azure OpenAI includes content safety systems to prevent misuse. For legal research queries about CPR and court procedures, this
                            typically has no impact. However, you should be aware:
                        </Text>
                        <Stack tokens={{ childrenGap: 8 }} style={{ marginTop: 8 }}>
                            <Text block>
                                • <strong>Automated filtering:</strong> AI classifiers check for harmful content in real-time. This filtering does not store
                                your queries.
                            </Text>
                            <Text block>
                                • <strong>Automated abuse detection:</strong> If content is flagged as potentially problematic, AI systems may review it. No
                                data is stored during automated review.
                            </Text>
                            <Text block>
                                • <strong>Human review (rare):</strong> In exceptional cases of suspected severe misuse, authorized Microsoft employees may
                                review flagged content using secure access controls. This is extremely unlikely for legitimate CPR research.
                            </Text>
                            <Text block>
                                • <strong>Enterprise option:</strong> Organizations can apply to Microsoft to disable human review for highly sensitive
                                workloads if required.
                            </Text>
                        </Stack>
                    </section>

                    {/* Best Practices for Lawyers */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="Lightbulb" className={styles.sectionIcon} />
                            Best Practices for Lawyers
                        </Text>
                        <Stack tokens={{ childrenGap: 8 }}>
                            <Text block>
                                ✅ <strong>Safe to use for:</strong> Researching CPR procedures, court rules, Practice Directions, costs rules, disclosure
                                requirements, case management, and general procedural questions.
                            </Text>
                            <Text block>
                                ⚠️ <strong>Recommendations:</strong>
                            </Text>
                            <Text block>• Avoid including real client names or case-specific identifiers when possible</Text>
                            <Text block>• Use generic placeholders for sensitive details (e.g., "the claimant" rather than specific names)</Text>
                            <Text block>• Always verify AI-generated citations against the source documents</Text>
                            <Text block>• Remember that AI responses are assistive, not authoritative legal advice</Text>
                        </Stack>
                    </section>

                    {/* Data Residency */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="Globe" className={styles.sectionIcon} />
                            Data Residency & Encryption
                        </Text>
                        <Stack tokens={{ childrenGap: 8 }}>
                            <Text block>• All data is processed within Microsoft Azure infrastructure</Text>
                            <Text block>• Data transmission is encrypted using TLS 1.2 or higher</Text>
                            <Text block>• Data at rest is encrypted using AES-256 encryption</Text>
                            <Text block>
                                • Azure region: <strong>East US 2</strong> (Note: This is a test environment. Production deployments can be configured for UK
                                South or West Europe)
                            </Text>
                        </Stack>
                    </section>

                    {/* Official Documentation Links */}
                    <section>
                        <Text variant="large" block className={styles.sectionTitle}>
                            <Icon iconName="BookAnswers" className={styles.sectionIcon} />
                            Official Microsoft Documentation
                        </Text>
                        <Stack tokens={{ childrenGap: 8 }}>
                            <Link
                                href="https://learn.microsoft.com/en-gb/azure/ai-services/openai/concepts/data-privacy"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Azure OpenAI Data, Privacy, and Security →
                            </Link>
                            <Link
                                href="https://learn.microsoft.com/en-gb/azure/ai-services/openai/concepts/abuse-monitoring"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Azure OpenAI Abuse Monitoring →
                            </Link>
                            <Link
                                href="https://learn.microsoft.com/en-gb/azure/ai-services/openai/faq#data-and-privacy"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Azure OpenAI FAQ: Data and Privacy →
                            </Link>
                            <Link href="https://www.microsoft.com/en-gb/trust-center" target="_blank" rel="noopener noreferrer">
                                Microsoft Trust Center →
                            </Link>
                        </Stack>
                    </section>

                    {/* Legal Disclaimer */}
                    <section className={styles.disclaimer}>
                        <Text variant="small" block>
                            <strong>Disclaimer:</strong> This summary is provided for informational purposes to help you understand how your data is handled
                            when using this Legal CPR Research Assistant. For complete and authoritative information about Microsoft's data handling practices,
                            please refer to the official Microsoft documentation linked above. AI-generated responses should always be verified against source
                            documents and are not a substitute for professional legal judgment.
                        </Text>
                    </section>
                </Stack>
            </Panel>
        </>
    );
};
