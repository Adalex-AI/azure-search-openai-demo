// Help & About Panel Component
// ==============================
// Provides comprehensive help, usage instructions, and privacy information
// for non-technical users of the Legal CPR Research Assistant.

import React, { useState } from "react";
import {
    Panel,
    PanelType,
    IconButton,
    Text,
    Stack,
    Pivot,
    PivotItem,
    Icon,
    mergeStyles,
    IIconProps,
    TooltipHost,
    DirectionalHint,
    Link
} from "@fluentui/react";

// Styles
const helpButtonStyle = mergeStyles({
    position: "fixed",
    top: "12px",
    left: "12px",
    zIndex: 1000,
    backgroundColor: "#0078d4",
    borderRadius: "50%",
    width: "44px",
    height: "44px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.2)",
    ":hover": {
        backgroundColor: "#106ebe"
    }
});

const panelContentStyle = mergeStyles({
    padding: "0 24px 24px 24px"
});

const sectionStyle = mergeStyles({
    marginBottom: "24px",
    padding: "16px",
    backgroundColor: "#f8f9fa",
    borderRadius: "8px",
    border: "1px solid #e1e4e8"
});

const featureBoxStyle = mergeStyles({
    padding: "16px",
    backgroundColor: "#fff",
    borderRadius: "8px",
    border: "1px solid #e1e4e8",
    marginBottom: "12px"
});

const iconBoxStyle = mergeStyles({
    width: "48px",
    height: "48px",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginRight: "16px",
    flexShrink: 0
});

const visualDiagramStyle = mergeStyles({
    padding: "20px",
    backgroundColor: "#fff",
    borderRadius: "8px",
    border: "2px solid #0078d4",
    fontFamily: "monospace",
    fontSize: "12px",
    lineHeight: "1.6",
    overflowX: "auto",
    whiteSpace: "pre"
});

const tipBoxStyle = mergeStyles({
    padding: "12px 16px",
    backgroundColor: "#fff4ce",
    borderLeft: "4px solid #ffb900",
    borderRadius: "0 8px 8px 0",
    marginBottom: "12px"
});

const warningBoxStyle = mergeStyles({
    padding: "12px 16px",
    backgroundColor: "#fde7e9",
    borderLeft: "4px solid #d13438",
    borderRadius: "0 8px 8px 0",
    marginBottom: "12px"
});

const stepNumberStyle = mergeStyles({
    width: "32px",
    height: "32px",
    borderRadius: "50%",
    backgroundColor: "#0078d4",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 600,
    marginRight: "12px",
    flexShrink: 0
});

interface FeatureCardProps {
    icon: string;
    iconColor: string;
    title: string;
    description: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, iconColor, title, description }) => (
    <div className={featureBoxStyle}>
        <Stack horizontal verticalAlign="start">
            <div className={iconBoxStyle} style={{ backgroundColor: iconColor + "20" }}>
                <Icon iconName={icon} styles={{ root: { fontSize: 24, color: iconColor } }} />
            </div>
            <Stack>
                <Text variant="mediumPlus" styles={{ root: { fontWeight: 600, marginBottom: 4 } }}>
                    {title}
                </Text>
                <Text variant="small" styles={{ root: { color: "#605e5c" } }}>
                    {description}
                </Text>
            </Stack>
        </Stack>
    </div>
);

interface StepProps {
    number: number;
    title: string;
    description: string;
}

const Step: React.FC<StepProps> = ({ number, title, description }) => (
    <Stack horizontal verticalAlign="start" styles={{ root: { marginBottom: 16 } }}>
        <div className={stepNumberStyle}>{number}</div>
        <Stack>
            <Text variant="medium" styles={{ root: { fontWeight: 600 } }}>
                {title}
            </Text>
            <Text variant="small" styles={{ root: { color: "#605e5c" } }}>
                {description}
            </Text>
        </Stack>
    </Stack>
);

export const HelpAboutPanel: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);

    const helpIcon: IIconProps = { iconName: "Help", styles: { root: { color: "#fff", fontSize: 20 } } };

    return (
        <>
            {/* Help Button - Top Left */}
            <TooltipHost content="Help & About" directionalHint={DirectionalHint.rightCenter}>
                <div className={helpButtonStyle}>
                    <IconButton iconProps={helpIcon} onClick={() => setIsOpen(true)} ariaLabel="Help and About" />
                </div>
            </TooltipHost>

            {/* Main Panel */}
            <Panel
                isOpen={isOpen}
                onDismiss={() => setIsOpen(false)}
                type={PanelType.medium}
                headerText="Legal CPR Research Assistant"
                closeButtonAriaLabel="Close"
                styles={{
                    main: { maxWidth: "600px" },
                    headerText: { fontSize: "20px", fontWeight: 600 }
                }}
            >
                <div className={panelContentStyle}>
                    <Pivot>
                        {/* About Tab */}
                        <PivotItem headerText="About" itemIcon="Info">
                            <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: 16 } }}>
                                <div className={sectionStyle}>
                                    <Text variant="large" styles={{ root: { fontWeight: 600, marginBottom: 12, display: "block" } }}>
                                        🔨 What is this tool?
                                    </Text>
                                    <Text>
                                        This AI-powered research assistant helps you search and query the <strong>Civil Procedure Rules (CPR)</strong>, Practice
                                        Directions, and Court Guides for England and Wales.
                                    </Text>
                                </div>

                                <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                                    📚 Document Sources
                                </Text>
                                <Stack tokens={{ childrenGap: 8 }}>
                                    <FeatureCard
                                        icon="Library"
                                        iconColor="#0078d4"
                                        title="Civil Procedure Rules"
                                        description="Parts 1-89 and all associated Practice Directions"
                                    />
                                    <FeatureCard icon="CityNext" iconColor="#107c10" title="Commercial Court Guide" description="11th Edition (July 2023)" />
                                    <FeatureCard icon="Courthouse" iconColor="#5c2d91" title="King's Bench Division Guide" description="2025 Edition" />
                                    <FeatureCard icon="Certificate" iconColor="#008272" title="Chancery Guide" description="2022 Edition" />
                                    <FeatureCard icon="Lightbulb" iconColor="#ff8c00" title="Patents Court Guide" description="February 2025" />
                                    <FeatureCard
                                        icon="ConstructionCone"
                                        iconColor="#d83b01"
                                        title="Technology & Construction Court Guide"
                                        description="October 2022"
                                    />
                                    <FeatureCard icon="Money" iconColor="#004e8c" title="Circuit Commercial Court Guide" description="August 2023" />
                                </Stack>
                            </Stack>
                        </PivotItem>

                        {/* How It Works Tab */}
                        <PivotItem headerText="How It Works" itemIcon="Lightbulb">
                            <Stack tokens={{ childrenGap: 20 }} styles={{ root: { marginTop: 16 } }}>
                                <div className={sectionStyle}>
                                    <Text variant="large" styles={{ root: { fontWeight: 600, marginBottom: 16, display: "block" } }}>
                                        🔄 Query Process
                                    </Text>
                                    <Step number={1} title="You Ask a Question" description="Type your legal research question in plain English" />
                                    <Step
                                        number={2}
                                        title="AI Searches Documents"
                                        description="Azure AI Search finds relevant passages from CPR, Practice Directions & Court Guides"
                                    />
                                    <Step
                                        number={3}
                                        title="AI Generates Answer"
                                        description="GPT-5-nano creates a response based ONLY on the retrieved documents"
                                    />
                                    <Step number={4} title="Citations Added" description="Each claim is linked to the source document for verification" />
                                </div>

                                <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                                    📊 Visual Flow
                                </Text>
                                <div className={visualDiagramStyle}>
                                    {`┌─────────────────┐
│  Your Question  │
│ "What are the   │
│  disclosure     │
│  obligations?"  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Azure AI       │
│  Search         │◄──── CPR Parts 1-89
│  (finds         │◄──── Practice Directions
│   relevant      │◄──── Court Guides
│   passages)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GPT-5-nano     │
│  (generates     │
│   answer from   │
│   retrieved     │
│   sources ONLY) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Answer with    │
│  Citations      │
│  [1][2][3]      │
└─────────────────┘`}
                                </div>
                            </Stack>
                        </PivotItem>

                        {/* Features Tab */}
                        <PivotItem headerText="Features" itemIcon="ViewAll">
                            <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: 16 } }}>
                                {/* Citations */}
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    📝 Understanding Citations
                                </Text>
                                <div className={sectionStyle}>
                                    <Text styles={{ root: { marginBottom: 12, display: "block" } }}>
                                        Every answer includes numbered citations like <strong>[1]</strong>, <strong>[2]</strong>, <strong>[3]</strong> that link
                                        to source documents.
                                    </Text>
                                    <div
                                        style={{
                                            padding: "12px",
                                            backgroundColor: "#fff",
                                            borderRadius: "8px",
                                            border: "1px solid #0078d4"
                                        }}
                                    >
                                        <Text styles={{ root: { fontStyle: "italic" } }}>
                                            "Standard disclosure requires a party to disclose documents on which it relies{" "}
                                            <span style={{ backgroundColor: "#deecf9", padding: "2px 6px", borderRadius: "4px" }}>[1]</span>, documents which
                                            adversely affect its case{" "}
                                            <span style={{ backgroundColor: "#deecf9", padding: "2px 6px", borderRadius: "4px" }}>[2]</span>, and documents
                                            which support another party's case{" "}
                                            <span style={{ backgroundColor: "#deecf9", padding: "2px 6px", borderRadius: "4px" }}>[3]</span>
                                            ."
                                        </Text>
                                    </div>
                                    <Stack horizontal tokens={{ childrenGap: 8 }} styles={{ root: { marginTop: 12 } }}>
                                        <Icon iconName="TouchPointer" styles={{ root: { color: "#0078d4" } }} />
                                        <Text variant="small">
                                            <strong>Click any citation number</strong> to view the source document
                                        </Text>
                                    </Stack>
                                </div>

                                {/* Supporting Content */}
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    📄 Supporting Content Panel
                                </Text>
                                <div className={sectionStyle}>
                                    <Stack horizontal tokens={{ childrenGap: 16 }}>
                                        <div
                                            style={{
                                                width: "60px",
                                                height: "80px",
                                                backgroundColor: "#f0f0f0",
                                                border: "1px solid #ccc",
                                                borderRadius: "4px",
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "center"
                                            }}
                                        >
                                            <Icon iconName="TextDocument" styles={{ root: { fontSize: 24, color: "#666" } }} />
                                        </div>
                                        <Stack>
                                            <Text styles={{ root: { fontWeight: 600 } }}>What is it?</Text>
                                            <Text variant="small">The exact text passages from CPR documents that the AI used to generate its answer.</Text>
                                            <Text variant="small" styles={{ root: { marginTop: 8 } }}>
                                                <strong>This is the PRIMARY SOURCE</strong> - always verify the AI's interpretation against these original
                                                passages.
                                            </Text>
                                        </Stack>
                                    </Stack>
                                </div>

                                {/* Thought Process */}
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    🧠 Thought Process
                                </Text>
                                <div className={sectionStyle}>
                                    <Text styles={{ root: { marginBottom: 12, display: "block" } }}>
                                        Click <strong>"Show thought process"</strong> to see:
                                    </Text>
                                    <Stack tokens={{ childrenGap: 8 }}>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="Search" styles={{ root: { color: "#0078d4" } }} />
                                            <Text variant="small">What search queries were used</Text>
                                        </Stack>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="Filter" styles={{ root: { color: "#0078d4" } }} />
                                            <Text variant="small">Which documents were retrieved</Text>
                                        </Stack>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="Processing" styles={{ root: { color: "#0078d4" } }} />
                                            <Text variant="small">How the AI processed the information</Text>
                                        </Stack>
                                    </Stack>
                                </div>

                                {/* Category Filter */}
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    🏷️ Category Filter
                                </Text>
                                <div className={sectionStyle}>
                                    <Text styles={{ root: { marginBottom: 12, display: "block" } }}>
                                        Use the dropdown to narrow your search to specific document types:
                                    </Text>
                                    <Stack tokens={{ childrenGap: 4 }}>
                                        <Text variant="small">• CPR Rules only</Text>
                                        <Text variant="small">• Practice Directions only</Text>
                                        <Text variant="small">• Specific Court Guides</Text>
                                        <Text variant="small">• All documents (default)</Text>
                                    </Stack>
                                </div>

                                {/* Feedback */}
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    👍👎 Feedback Buttons
                                </Text>
                                <div className={sectionStyle}>
                                    <Text styles={{ root: { marginBottom: 12, display: "block" } }}>Help improve the tool by rating responses:</Text>
                                    <Stack horizontal tokens={{ childrenGap: 24 }}>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="Like" styles={{ root: { color: "#107c10", fontSize: 20 } }} />
                                            <Text variant="small">Accurate & helpful</Text>
                                        </Stack>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="Dislike" styles={{ root: { color: "#d13438", fontSize: 20 } }} />
                                            <Text variant="small">Inaccurate or unhelpful</Text>
                                        </Stack>
                                    </Stack>
                                    <Text variant="small" styles={{ root: { marginTop: 12, color: "#605e5c" } }}>
                                        You can optionally share your query to help us understand issues.
                                    </Text>
                                </div>
                            </Stack>
                        </PivotItem>

                        {/* Tips Tab */}
                        <PivotItem headerText="Tips" itemIcon="LightningBolt">
                            <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: 16 } }}>
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    ✅ Best Practices
                                </Text>

                                <div className={tipBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                        <Text variant="small">
                                            <strong>Be specific:</strong> "What is the time limit for filing an acknowledgment of service?"
                                        </Text>
                                    </Stack>
                                </div>

                                <div className={tipBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                        <Text variant="small">
                                            <strong>Use legal terminology:</strong> "disclosure obligations" rather than "sharing documents"
                                        </Text>
                                    </Stack>
                                </div>

                                <div className={tipBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                        <Text variant="small">
                                            <strong>Always verify:</strong> Click citations to check the source text matches the AI's summary
                                        </Text>
                                    </Stack>
                                </div>

                                <div className={tipBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                        <Text variant="small">
                                            <strong>Use follow-up questions:</strong> The chat remembers context from your conversation
                                        </Text>
                                    </Stack>
                                </div>

                                <Text variant="large" styles={{ root: { fontWeight: 600, marginTop: 12 } }}>
                                    ⚠️ Important Warnings
                                </Text>

                                <div className={warningBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="Warning" styles={{ root: { color: "#d13438" } }} />
                                        <Text variant="small">
                                            <strong>Not for deadline calculations:</strong> Always verify deadlines via official court channels
                                        </Text>
                                    </Stack>
                                </div>

                                <div className={warningBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="Warning" styles={{ root: { color: "#d13438" } }} />
                                        <Text variant="small">
                                            <strong>AI can make mistakes:</strong> Responses are assistive, not authoritative legal advice
                                        </Text>
                                    </Stack>
                                </div>

                                <div className={warningBoxStyle}>
                                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                        <Icon iconName="Warning" styles={{ root: { color: "#d13438" } }} />
                                        <Text variant="small">
                                            <strong>Check currency:</strong> Verify Practice Direction dates are current before relying on them
                                        </Text>
                                    </Stack>
                                </div>

                                <Text variant="large" styles={{ root: { fontWeight: 600, marginTop: 12 } }}>
                                    💡 Example Queries
                                </Text>
                                <div className={sectionStyle}>
                                    <Stack tokens={{ childrenGap: 8 }}>
                                        <Text variant="small" styles={{ root: { fontStyle: "italic" } }}>
                                            "What are the requirements for standard disclosure under CPR Part 31?"
                                        </Text>
                                        <Text variant="small" styles={{ root: { fontStyle: "italic" } }}>
                                            "How do I apply for summary judgment?"
                                        </Text>
                                        <Text variant="small" styles={{ root: { fontStyle: "italic" } }}>
                                            "What are the cost budgeting requirements in the Commercial Court?"
                                        </Text>
                                        <Text variant="small" styles={{ root: { fontStyle: "italic" } }}>
                                            "Explain the pre-action protocol requirements for professional negligence claims"
                                        </Text>
                                    </Stack>
                                </div>
                            </Stack>
                        </PivotItem>

                        {/* Privacy Tab */}
                        <PivotItem headerText="Privacy" itemIcon="Shield">
                            <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: 16 } }}>
                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    🛡️ Data Protection
                                </Text>

                                <div className={sectionStyle}>
                                    <Stack tokens={{ childrenGap: 12 }}>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                            <Text variant="small">
                                                <strong>NOT used for AI training:</strong> Your queries never train AI models
                                            </Text>
                                        </Stack>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                            <Text variant="small">
                                                <strong>NOT shared:</strong> Your queries are isolated - others cannot see them
                                            </Text>
                                        </Stack>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                            <Text variant="small">
                                                <strong>NOT sent to OpenAI:</strong> Uses Azure OpenAI (separate enterprise service)
                                            </Text>
                                        </Stack>
                                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                            <Icon iconName="CheckMark" styles={{ root: { color: "#107c10" } }} />
                                            <Text variant="small">
                                                <strong>NOT stored:</strong> No chat history is retained after your session
                                            </Text>
                                        </Stack>
                                    </Stack>
                                </div>

                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    💾 What is Stored
                                </Text>
                                <div className={sectionStyle}>
                                    <Stack tokens={{ childrenGap: 8 }}>
                                        <Text variant="small">
                                            <strong>Legal documents:</strong> CPR, Practice Directions, Court Guides (permanent)
                                        </Text>
                                        <Text variant="small">
                                            <strong>Feedback (optional):</strong> Only if you submit feedback and consent to share your query
                                        </Text>
                                        <Text variant="small">
                                            <strong>Your queries:</strong> NOT stored - discarded after processing
                                        </Text>
                                    </Stack>
                                </div>

                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    ⚙️ Technical Details
                                </Text>
                                <div className={sectionStyle}>
                                    <Stack tokens={{ childrenGap: 8 }}>
                                        <Text variant="small">
                                            <strong>AI Model:</strong> GPT-5-nano via Azure OpenAI
                                        </Text>
                                        <Text variant="small">
                                            <strong>Region:</strong> East US 2 (test environment)
                                        </Text>
                                        <Text variant="small">
                                            <strong>Encryption:</strong> TLS 1.2+ in transit, AES-256 at rest
                                        </Text>
                                    </Stack>
                                </div>

                                <Text variant="large" styles={{ root: { fontWeight: 600 } }}>
                                    📚 Official Documentation
                                </Text>
                                <Stack tokens={{ childrenGap: 8 }}>
                                    <Link
                                        href="https://learn.microsoft.com/en-gb/legal/cognitive-services/openai/data-privacy"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        Azure OpenAI Data, Privacy & Security →
                                    </Link>
                                    <Link href="https://www.microsoft.com/en-gb/trust-center" target="_blank" rel="noopener noreferrer">
                                        Microsoft Trust Center (UK) →
                                    </Link>
                                </Stack>
                            </Stack>
                        </PivotItem>
                    </Pivot>
                </div>
            </Panel>
        </>
    );
};
