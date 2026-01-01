import { useContext, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Helmet } from "react-helmet-async";
import { Panel, DefaultButton, Spinner, Dropdown, IDropdownOption } from "@fluentui/react";

import styles from "./Ask.module.css";

import { askApi, configApi, ChatAppResponse, ChatAppRequest, RetrievalMode, VectorFields, GPT4VInput, SpeechConfig } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { ExampleList } from "../../components/Example";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";
import { useLogin, getToken, requireAccessControl } from "../../authConfig";
import { UploadFile } from "../../components/UploadFile";
import { Settings } from "../../components/Settings/Settings";
import { useMsal } from "@azure/msal-react";
import { TokenClaimsDisplay } from "../../components/TokenClaimsDisplay";
import { LoginContext } from "../../loginContext";
import { LanguagePicker } from "../../i18n/LanguagePicker";
// CUSTOM: Import from customizations folder for merge-safe architecture
import { useCategories, isIframeBlocked, HelpAboutPanel, isAdminMode, useIsMobile } from "../../customizations";

// CUSTOM: Check admin mode for showing developer settings
const adminMode = isAdminMode();

export function Component(): JSX.Element {
    // CUSTOM: Mobile detection for responsive UI
    const isMobile = useIsMobile();

    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplatePrefix, setPromptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix, setPromptTemplateSuffix] = useState<string>("");
    const [temperature, setTemperature] = useState<number>(0.3);
    const [seed, setSeed] = useState<number | null>(null);
    const [minimumRerankerScore, setMinimumRerankerScore] = useState<number>(0);
    const [minimumSearchScore, setMinimumSearchScore] = useState<number>(0);
    const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>(RetrievalMode.Hybrid);
    const [retrieveCount, setRetrieveCount] = useState<number>(5);
    const [maxSubqueryCount, setMaxSubqueryCount] = useState<number>(5);
    const [resultsMergeStrategy, setResultsMergeStrategy] = useState<string>("interleaved");
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [useQueryRewriting, setUseQueryRewriting] = useState<boolean>(false);
    const [reasoningEffort, setReasoningEffort] = useState<string>("low");
    const [useGPT4V, setUseGPT4V] = useState<boolean>(false);
    const [gpt4vInput, setGPT4VInput] = useState<GPT4VInput>(GPT4VInput.TextAndImages);
    const [includeCategory, setIncludeCategory] = useState<string>("");
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [question, setQuestion] = useState<string>("");
    const [vectorFields, setVectorFields] = useState<VectorFields>(VectorFields.TextAndImageEmbeddings);
    const [useOidSecurityFilter, setUseOidSecurityFilter] = useState<boolean>(false);
    const [useGroupsSecurityFilter, setUseGroupsSecurityFilter] = useState<boolean>(false);
    const [showGPT4VOptions, setShowGPT4VOptions] = useState<boolean>(false);
    const [showSemanticRankerOption, setShowSemanticRankerOption] = useState<boolean>(false);
    const [showQueryRewritingOption, setShowQueryRewritingOption] = useState<boolean>(false);
    const [showReasoningEffortOption, setShowReasoningEffortOption] = useState<boolean>(false);
    const [showVectorOption, setShowVectorOption] = useState<boolean>(false);
    const [showUserUpload, setShowUserUpload] = useState<boolean>(false);
    const [showLanguagePicker, setshowLanguagePicker] = useState<boolean>(false);
    const [showSpeechInput, setShowSpeechInput] = useState<boolean>(false);
    const [showSpeechOutputBrowser, setShowSpeechOutputBrowser] = useState<boolean>(false);
    const [showSpeechOutputAzure, setShowSpeechOutputAzure] = useState<boolean>(false);
    const audio = useRef(new Audio()).current;
    const [isPlaying, setIsPlaying] = useState(false);
    const [showAgenticRetrievalOption, setShowAgenticRetrievalOption] = useState<boolean>(false);
    const [useAgenticRetrieval, setUseAgenticRetrieval] = useState<boolean>(true);
    const [showCategoryFilter, setShowCategoryFilter] = useState<boolean>(false);

    const lastQuestionRef = useRef<string>("");

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<ChatAppResponse>();
    // For the Ask tab, this array will hold a maximum of one URL
    const [speechUrls, setSpeechUrls] = useState<(string | null)[]>([]);

    const speechConfig: SpeechConfig = {
        speechUrls,
        setSpeechUrls,
        audio,
        isPlaying,
        setIsPlaying
    };

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeCitationContent, setActiveCitationContent] = useState<string>(); // New state
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);
    const [enableCitationTab, setEnableCitationTab] = useState(false);

    const client = useLogin ? useMsal().instance : undefined;
    const { loggedIn } = useContext(LoginContext);

    const getConfig = async () => {
        configApi().then(config => {
            setShowGPT4VOptions(config.showGPT4VOptions);
            setUseSemanticRanker(config.showSemanticRankerOption);
            setShowSemanticRankerOption(config.showSemanticRankerOption);
            setUseQueryRewriting(config.showQueryRewritingOption);
            setShowQueryRewritingOption(config.showQueryRewritingOption);
            setShowReasoningEffortOption(config.showReasoningEffortOption);
            if (config.showReasoningEffortOption && config.defaultReasoningEffort) {
                setReasoningEffort(config.defaultReasoningEffort);
            }
            setShowVectorOption(config.showVectorOption);
            if (!config.showVectorOption) {
                setRetrievalMode(RetrievalMode.Text);
            }
            setShowUserUpload(config.showUserUpload);
            setshowLanguagePicker(config.showLanguagePicker);
            setShowSpeechInput(config.showSpeechInput);
            setShowSpeechOutputBrowser(config.showSpeechOutputBrowser);
            setShowSpeechOutputAzure(config.showSpeechOutputAzure);
            setShowAgenticRetrievalOption(config.showAgenticRetrievalOption);
            // 'showCategoryFilter' may not exist on older/alternate Config types — cast to any to safely read optional field
            setShowCategoryFilter(!!(config as any).showCategoryFilter);
        });
    };

    useEffect(() => {
        getConfig();
    }, []);

    // Add state for category confirmation and user interaction tracking
    const [categoryConfirmed, setCategoryConfirmed] = useState<boolean>(true); // Start as true
    const [userTriedToSearch, setUserTriedToSearch] = useState<boolean>(false); // Track search attempts
    const [userHasInteracted, setUserHasInteracted] = useState<boolean>(false); // Track if user interacted with the category dropdown
    const [allCategoriesSelected, setAllCategoriesSelected] = useState<boolean>(false);

    // Load categories
    const { categories, loading: categoriesLoading } = useCategories();
    const categoryOptions: IDropdownOption[] = [
        { key: "", text: "All Sources" },
        ...categories.filter(c => typeof c?.key === "string" && typeof c?.text === "string" && c.key !== "").map(c => ({ key: c.key, text: c.text }))
    ];

    const includeKeys = includeCategory
        ? includeCategory
              .split(",")
              .map(s => s.trim())
              .filter(Boolean)
        : [];

    const onIncludeCategoryChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IDropdownOption) => {
        if (!option) return;

        const key = String(option.key || "");
        if (key === "") {
            // Toggle All tick
            setAllCategoriesSelected(!!option.selected);
            setUserHasInteracted(true);
            setUserTriedToSearch(false);
            handleSettingsChange("includeCategory", "");
            return;
        }

        // Selecting specific category clears "All"
        setAllCategoriesSelected(false);

        let next = includeKeys.slice();
        if (option.selected) {
            if (!next.includes(key)) next.push(key);
        } else {
            next = next.filter(k => k !== key);
        }

        const newValue = next.join(",");
        setUserHasInteracted(true);
        setUserTriedToSearch(false);
        handleSettingsChange("includeCategory", newValue);

        // If user deselects all categories (empty selection), require new interaction
        if (newValue === "" && !allCategoriesSelected) {
            setUserHasInteracted(false);
        }
    };

    // Add useEffect to handle category confirmation properly
    useEffect(() => {
        if (showCategoryFilter) {
            // Category is confirmed if user has selected anything (including empty string for "All")
            setCategoryConfirmed(true); // Always confirmed when category filter is shown
        } else {
            setCategoryConfirmed(true);
        }
    }, [includeCategory, showCategoryFilter]);

    const makeApiRequest = async (question: string) => {
        // Block search if no category is selected and "All" isn't ticked
        if (showCategoryFilter && includeCategory.trim() === "" && !allCategoriesSelected) {
            setUserTriedToSearch(true);
            return; // Don't proceed with search
        }

        setUserTriedToSearch(false);
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        const token = client ? await getToken(client) : undefined;

        try {
            const request: ChatAppRequest = {
                messages: [
                    {
                        content: question,
                        role: "user"
                    }
                ],
                context: {
                    overrides: {
                        prompt_template: promptTemplate.length === 0 ? undefined : promptTemplate,
                        prompt_template_prefix: promptTemplatePrefix.length === 0 ? undefined : promptTemplatePrefix,
                        prompt_template_suffix: promptTemplateSuffix.length === 0 ? undefined : promptTemplateSuffix,
                        include_category: includeCategory.length === 0 ? undefined : includeCategory,
                        exclude_category: excludeCategory.length === 0 ? undefined : excludeCategory,
                        top: retrieveCount,
                        max_subqueries: maxSubqueryCount,
                        results_merge_strategy: resultsMergeStrategy,
                        temperature: temperature,
                        minimum_reranker_score: minimumRerankerScore,
                        minimum_search_score: minimumSearchScore,
                        retrieval_mode: retrievalMode,
                        semantic_ranker: useSemanticRanker,
                        semantic_captions: useSemanticCaptions,
                        query_rewriting: useQueryRewriting,
                        reasoning_effort: reasoningEffort,
                        use_oid_security_filter: useOidSecurityFilter,
                        use_groups_security_filter: useGroupsSecurityFilter,
                        vector_fields: vectorFields,
                        use_gpt4v: useGPT4V,
                        gpt4v_input: gpt4vInput,
                        language: i18n.language,
                        use_agentic_retrieval: useAgenticRetrieval,
                        ...(seed !== null ? { seed: seed } : {})
                    }
                },
                // AI Chat Protocol: Client must pass on any session state received from the server
                session_state: answer ? answer.session_state : null
            };
            const result = await askApi(request, token);
            setAnswer(result);
            setSpeechUrls([null]);
        } catch (e) {
            console.error("API request failed:", e);
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSettingsChange = (field: string, value: any) => {
        switch (field) {
            case "promptTemplate":
                setPromptTemplate(value);
                break;
            case "promptTemplatePrefix":
                setPromptTemplatePrefix(value);
                break;
            case "promptTemplateSuffix":
                setPromptTemplateSuffix(value);
                break;
            case "temperature":
                setTemperature(value);
                break;
            case "seed":
                setSeed(value);
                break;
            case "minimumRerankerScore":
                setMinimumRerankerScore(value);
                break;
            case "minimumSearchScore":
                setMinimumSearchScore(value);
                break;
            case "retrieveCount":
                setRetrieveCount(value);
                break;
            case "maxSubqueryCount":
                setMaxSubqueryCount(value);
                break;
            case "resultsMergeStrategy":
                setResultsMergeStrategy(value);
                break;
            case "useSemanticRanker":
                setUseSemanticRanker(value);
                break;
            case "useSemanticCaptions":
                setUseSemanticCaptions(value);
                break;
            case "useQueryRewriting":
                setUseQueryRewriting(value);
                break;
            case "reasoningEffort":
                setReasoningEffort(value);
                break;
            case "excludeCategory":
                setExcludeCategory(value);
                break;
            case "includeCategory":
                setIncludeCategory(value);
                setUserHasInteracted(true); // Mark that user has interacted
                setUserTriedToSearch(false); // Clear any previous warning
                break;
            case "useOidSecurityFilter":
                setUseOidSecurityFilter(value);
                break;
            case "useGroupsSecurityFilter":
                setUseGroupsSecurityFilter(value);
                break;
            case "useGPT4V":
                setUseGPT4V(value);
                break;
            case "gpt4vInput":
                setGPT4VInput(value);
                break;
            case "vectorFields":
                setVectorFields(value);
                break;
            case "retrievalMode":
                setRetrievalMode(value);
                break;
            case "useAgenticRetrieval":
                setUseAgenticRetrieval(value);
        }
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
        setQuestion(example);
    };

    const onShowCitation = (citation: string, citationContent?: string) => {
        console.log("onShowCitation called with:", { citation, citationContent: citationContent ? "content provided" : "no content" });

        // CUSTOM: Check if citation is blocked from iframe embedding
        if (isIframeBlocked(citation)) {
            window.open(citation, "_blank", "noopener,noreferrer");
            return;
        }

        // Always show supporting content tab when citation is clicked
        setActiveCitation(citation);

        // Store the full citation content, not just a preview
        setActiveCitationContent(citationContent || "");
        setActiveAnalysisPanelTab(AnalysisPanelTabs.SupportingContentTab);
        setEnableCitationTab(false); // Disable citation tab by default
    };

    const onToggleTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab === tab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            // Enable citation tab when explicitly requested
            if (tab === AnalysisPanelTabs.CitationTab) {
                setEnableCitationTab(true);
            }
            setActiveAnalysisPanelTab(tab);
        }
    };

    const onUseOidSecurityFilterChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseOidSecurityFilter(!!checked);
    };

    const onUseGroupsSecurityFilterChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseGroupsSecurityFilter(!!checked);
    };

    const { t, i18n } = useTranslation();

    // Disable submit if category not confirmed
    const isSubmitDisabled = isLoading || !categoryConfirmed;

    return (
        <div className={styles.askContainer}>
            {/* Setting the page title using react-helmet-async */}
            <Helmet>
                <title>{t("pageTitle")}</title>
            </Helmet>
            <div className={styles.askTopSection}>
                <div className={styles.commandsContainer}>
                    {showUserUpload && <UploadFile className={styles.commandButton} disabled={!loggedIn} />}
                    {/* CUSTOM: Only show settings button in admin mode (add ?admin=true to URL) */}
                    {adminMode && <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />}
                </div>
                <h1 className={styles.askTitle}>{t("askTitle")}</h1>
                <div className={styles.askQuestionInput}>
                    <QuestionInput
                        placeholder={t("gpt4vExamples.placeholder")}
                        disabled={isLoading}
                        initQuestion={question}
                        onSend={question => makeApiRequest(question)}
                        showSpeechInput={showSpeechInput}
                        leftOfSend={
                            showCategoryFilter ? (
                                <Dropdown
                                    multiSelect
                                    styles={{
                                        dropdown: {
                                            minWidth: 220,
                                            minHeight: 48
                                        },
                                        title: {
                                            minHeight: 48,
                                            display: "flex",
                                            alignItems: "center",
                                            paddingTop: 10,
                                            paddingBottom: 10,
                                            fontSize: 16
                                        },
                                        caretDownWrapper: {
                                            height: 48,
                                            display: "flex",
                                            alignItems: "center"
                                        },
                                        callout: {
                                            minWidth: 350,
                                            maxWidth: 500,
                                            width: "auto"
                                        },
                                        dropdownItem: {
                                            minHeight: "auto",
                                            height: "auto",
                                            padding: "12px 12px",
                                            whiteSpace: "normal",
                                            overflow: "visible",
                                            textOverflow: "initial",
                                            wordWrap: "break-word"
                                        },
                                        dropdownOptionText: {
                                            whiteSpace: "normal",
                                            overflow: "visible",
                                            textOverflow: "initial",
                                            wordWrap: "break-word",
                                            lineHeight: "24px",
                                            fontSize: 16
                                        }
                                    }}
                                    options={categoryOptions}
                                    selectedKeys={allCategoriesSelected ? [""] : includeKeys}
                                    onChange={onIncludeCategoryChange}
                                    disabled={isLoading || categoriesLoading}
                                    placeholder="Select sources or All"
                                />
                            ) : undefined
                        }
                    />
                    {showCategoryFilter && userTriedToSearch && !userHasInteracted && (
                        <div className={styles.categoryWarning}>Please select a source before searching. Choose "All Sources" to search all documents.</div>
                    )}
                </div>
            </div>
            <div className={styles.askBottomSection}>
                {isLoading && <Spinner label={t("generatingAnswer")} />}
                {!lastQuestionRef.current && (
                    <div className={styles.askTopSection}>
                        {showLanguagePicker && <LanguagePicker onLanguageChange={newLang => i18n.changeLanguage(newLang)} />}
                        <ExampleList onExampleClicked={onExampleClicked} useGPT4V={useGPT4V} />
                    </div>
                )}
                {!isLoading && answer && !error && (
                    <div className={styles.askAnswerContainer}>
                        <Answer
                            answer={answer}
                            index={0}
                            speechConfig={speechConfig}
                            isStreaming={false}
                            onCitationClicked={onShowCitation}
                            onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                            onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                            showSpeechOutputAzure={showSpeechOutputAzure}
                            showSpeechOutputBrowser={showSpeechOutputBrowser}
                            userPrompt={lastQuestionRef.current}
                            conversationHistory={[
                                { role: "user", content: lastQuestionRef.current },
                                { role: "assistant", content: answer.message?.content || "" }
                            ]}
                        />
                    </div>
                )}
                {error ? (
                    <div className={styles.askAnswerContainer}>
                        <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                    </div>
                ) : null}

                {/* Mobile: Modal overlay for analysis panel */}
                {isMobile && activeAnalysisPanelTab && answer && (
                    <>
                        {/* Overlay backdrop */}
                        <div className={styles.mobileAnalysisOverlay} onClick={() => setActiveAnalysisPanelTab(undefined)} />
                        {/* Modal panel */}
                        <div className={styles.mobileAnalysisModal}>
                            {/* Close button */}
                            <div className={styles.mobileAnalysisHeader}>
                                <button
                                    className={styles.mobileAnalysisCloseButton}
                                    onClick={() => setActiveAnalysisPanelTab(undefined)}
                                    aria-label="Close supporting content"
                                >
                                    ✕
                                </button>
                            </div>
                            <AnalysisPanel
                                className={styles.askAnalysisPanelMobile}
                                activeCitation={activeCitation}
                                onActiveTabChanged={x => onToggleTab(x)}
                                citationHeight="calc(85vh - 60px)"
                                answer={answer}
                                activeTab={activeAnalysisPanelTab}
                                activeCitationContent={activeCitationContent}
                                enableCitationTab={enableCitationTab}
                                onCitationChanged={setActiveCitation}
                            />
                        </div>
                    </>
                )}

                {/* Desktop: Analysis panel on the right */}
                {!isMobile && activeAnalysisPanelTab && answer && (
                    <AnalysisPanel
                        className={styles.askAnalysisPanel}
                        activeCitation={activeCitation}
                        onActiveTabChanged={x => onToggleTab(x)}
                        citationHeight="600px"
                        answer={answer}
                        activeTab={activeAnalysisPanelTab}
                        activeCitationContent={activeCitationContent}
                        enableCitationTab={enableCitationTab}
                        onCitationChanged={setActiveCitation}
                    />
                )}
            </div>

            <Panel
                headerText={t("labels.headerText")}
                isOpen={isConfigPanelOpen}
                isBlocking={false}
                onDismiss={() => setIsConfigPanelOpen(false)}
                closeButtonAriaLabel={t("labels.closeButton")}
                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>{t("labels.closeButton")}</DefaultButton>}
                isFooterAtBottom={true}
            >
                <Settings
                    promptTemplate={promptTemplate}
                    promptTemplatePrefix={promptTemplatePrefix}
                    promptTemplateSuffix={promptTemplateSuffix}
                    temperature={temperature}
                    retrieveCount={retrieveCount}
                    maxSubqueryCount={maxSubqueryCount}
                    resultsMergeStrategy={resultsMergeStrategy}
                    seed={seed}
                    minimumSearchScore={minimumSearchScore}
                    minimumRerankerScore={minimumRerankerScore}
                    useSemanticRanker={useSemanticRanker}
                    useSemanticCaptions={useSemanticCaptions}
                    useQueryRewriting={useQueryRewriting}
                    reasoningEffort={reasoningEffort}
                    excludeCategory={excludeCategory}
                    includeCategory={includeCategory}
                    retrievalMode={retrievalMode}
                    useGPT4V={useGPT4V}
                    gpt4vInput={gpt4vInput}
                    vectorFields={vectorFields}
                    showSemanticRankerOption={showSemanticRankerOption}
                    showQueryRewritingOption={showQueryRewritingOption}
                    showReasoningEffortOption={showReasoningEffortOption}
                    showGPT4VOptions={showGPT4VOptions}
                    showVectorOption={showVectorOption}
                    useOidSecurityFilter={useOidSecurityFilter}
                    useGroupsSecurityFilter={useGroupsSecurityFilter}
                    useLogin={!!useLogin}
                    loggedIn={loggedIn}
                    requireAccessControl={requireAccessControl}
                    showAgenticRetrievalOption={showAgenticRetrievalOption}
                    useAgenticRetrieval={useAgenticRetrieval}
                    onChange={handleSettingsChange}
                />
                {useLogin && <TokenClaimsDisplay />}
            </Panel>

            {/* CUSTOM: Help & About panel for lawyers testing the system */}
            <HelpAboutPanel />
        </div>
    );
}

Component.displayName = "Ask";
