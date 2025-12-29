import { useRef, useState, useEffect, useContext } from "react";
import { useTranslation } from "react-i18next";
import { Helmet } from "react-helmet-async";
import { Panel, DefaultButton, Dropdown, IDropdownOption, TooltipHost, IconButton, DirectionalHint } from "@fluentui/react";
import readNDJSONStream from "ndjson-readablestream";

import appLogo from "../../assets/applogo.svg";
import styles from "./Chat.module.css";

import {
    chatApi,
    configApi,
    RetrievalMode,
    ChatAppResponse,
    ChatAppResponseOrError,
    ChatAppRequest,
    ResponseMessage,
    VectorFields,
    GPT4VInput,
    SpeechConfig
} from "../../api";
import { Answer, AnswerError, AnswerLoading } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { ExampleList } from "../../components/Example";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { HistoryPanel } from "../../components/HistoryPanel";
import { HistoryProviderOptions, useHistoryManager } from "../../components/HistoryProviders";
import { HistoryButton } from "../../components/HistoryButton";
import { SettingsButton } from "../../components/SettingsButton";
import { ClearChatButton } from "../../components/ClearChatButton";
import { UploadFile } from "../../components/UploadFile";
import { useLogin, getToken, requireAccessControl } from "../../authConfig";
import { useMsal } from "@azure/msal-react";
import { TokenClaimsDisplay } from "../../components/TokenClaimsDisplay";
import { LoginContext } from "../../loginContext";
import { LanguagePicker } from "../../i18n/LanguagePicker";
import { Settings } from "../../components/Settings/Settings";
// CUSTOM: Import from customizations folder for merge-safe architecture
import { useCategories, DataPrivacyNotice } from "../../customizations";

import { isIframeBlocked } from "../../customizations";

const Chat = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [temperature, setTemperature] = useState<number>(0.3);
    const [seed, setSeed] = useState<number | null>(null);
    const [minimumRerankerScore, setMinimumRerankerScore] = useState<number>(0);
    const [minimumSearchScore, setMinimumSearchScore] = useState<number>(0);
    const [retrieveCount, setRetrieveCount] = useState<number>(5);
    const [maxSubqueryCount, setMaxSubqueryCount] = useState<number>(5);
    const [resultsMergeStrategy, setResultsMergeStrategy] = useState<string>("interleaved");
    const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>(RetrievalMode.Hybrid);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useQueryRewriting, setUseQueryRewriting] = useState<boolean>(false);
    const [reasoningEffort, setReasoningEffort] = useState<string>("low");
    const [streamingEnabled, setStreamingEnabled] = useState<boolean>(true);
    const [shouldStream, setShouldStream] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [includeCategory, setIncludeCategory] = useState<string>("");
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(false);
    const [vectorFields, setVectorFields] = useState<VectorFields>(VectorFields.TextAndImageEmbeddings);
    const [useOidSecurityFilter, setUseOidSecurityFilter] = useState<boolean>(false);
    const [useGroupsSecurityFilter, setUseGroupsSecurityFilter] = useState<boolean>(false);
    const [gpt4vInput, setGPT4VInput] = useState<GPT4VInput>(GPT4VInput.TextAndImages);
    const [useGPT4V, setUseGPT4V] = useState<boolean>(false);
    const [userHasInteracted, setUserHasInteracted] = useState<boolean>(false);
    const [userTriedToSearch, setUserTriedToSearch] = useState<boolean>(false);
    const [allCategoriesSelected, setAllCategoriesSelected] = useState<boolean>(false);

    const lastQuestionRef = useRef<string>("");
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isStreaming, setIsStreaming] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeCitationContent, setActiveCitationContent] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    // Add this new state for the citation label
    const [activeCitationLabel, setActiveCitationLabel] = useState<string>();

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: ChatAppResponse][]>([]);
    const [streamedAnswers, setStreamedAnswers] = useState<[user: string, response: ChatAppResponse][]>([]);
    const [speechUrls, setSpeechUrls] = useState<(string | null)[]>([]);

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
    const [showChatHistoryBrowser, setShowChatHistoryBrowser] = useState<boolean>(false);
    const [showChatHistoryCosmos, setShowChatHistoryCosmos] = useState<boolean>(false);
    const [showAgenticRetrievalOption, setShowAgenticRetrievalOption] = useState<boolean>(false);
    const [useAgenticRetrieval, setUseAgenticRetrieval] = useState<boolean>(true);
    const [showCategoryFilter, setShowCategoryFilter] = useState<boolean>(false);

    const audio = useRef(new Audio()).current;
    const [isPlaying, setIsPlaying] = useState(false);

    const speechConfig: SpeechConfig = {
        speechUrls,
        setSpeechUrls,
        audio,
        isPlaying,
        setIsPlaying
    };

    const getConfig = async () => {
        configApi().then((config: any) => {
            setShowGPT4VOptions(config.showGPT4VOptions);
            if (config.showGPT4VOptions) {
                setUseGPT4V(true);
            }
            setUseSemanticRanker(config.showSemanticRankerOption);
            setShowSemanticRankerOption(config.showSemanticRankerOption);
            setUseQueryRewriting(config.showQueryRewritingOption);
            setShowQueryRewritingOption(config.showQueryRewritingOption);
            setShowReasoningEffortOption(config.showReasoningEffortOption);
            setStreamingEnabled(config.streamingEnabled);
            if (!config.streamingEnabled) {
                setShouldStream(false);
            }
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
            setShowChatHistoryBrowser(config.showChatHistoryBrowser);
            setShowChatHistoryCosmos(config.showChatHistoryCosmos);
            setShowAgenticRetrievalOption(config.showAgenticRetrievalOption);
            setShowCategoryFilter(!!config.showCategoryFilter);
        });
    };

    const handleAsyncRequest = async (question: string, answers: [string, ChatAppResponse][], responseBody: ReadableStream<any>) => {
        let answer: string = "";
        let askResponse: ChatAppResponse = {} as ChatAppResponse;

        const updateState = (newContent: string) => {
            return new Promise(resolve => {
                setTimeout(() => {
                    answer += newContent;
                    const latestResponse: ChatAppResponse = {
                        ...askResponse,
                        message: { content: answer, role: askResponse.message.role }
                    };
                    setStreamedAnswers([...answers, [question, latestResponse]]);
                    resolve(null);
                }, 33);
            });
        };
        try {
            setIsStreaming(true);
            for await (const event of readNDJSONStream(responseBody)) {
                if (event["context"] && event["context"]["data_points"]) {
                    event["message"] = event["delta"];
                    askResponse = event as ChatAppResponse;
                } else if (event["delta"] && event["delta"]["content"]) {
                    setIsLoading(false);
                    await updateState(event["delta"]["content"]);
                } else if (event["context"]) {
                    // Update context with new keys from latest event
                    askResponse.context = { ...askResponse.context, ...event["context"] };
                } else if (event["error"]) {
                    throw Error(event["error"]);
                }
            }
        } finally {
            setIsStreaming(false);
        }
        const fullResponse: ChatAppResponse = {
            ...askResponse,
            message: { content: answer, role: askResponse.message.role }
        };
        return fullResponse;
    };

    const client = useLogin ? useMsal().instance : undefined;
    const { loggedIn } = useContext(LoginContext);

    const historyProvider: HistoryProviderOptions = (() => {
        if (useLogin && showChatHistoryCosmos) return HistoryProviderOptions.CosmosDB;
        if (showChatHistoryBrowser) return HistoryProviderOptions.IndexedDB;
        return HistoryProviderOptions.None;
    })();
    const historyManager = useHistoryManager(historyProvider);

    const makeApiRequest = async (question: string) => {
        // Block search if no category is selected and "All" isn't ticked
        if (showCategoryFilter && includeCategory.trim() === "" && !allCategoriesSelected) {
            setUserTriedToSearch(true);
            return;
        }
        setUserTriedToSearch(false);

        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        const token = client ? await getToken(client) : undefined;

        try {
            const messages: ResponseMessage[] = answers.flatMap(a => [
                { content: a[0], role: "user" },
                { content: a[1].message.content, role: "assistant" }
            ]);

            const request: ChatAppRequest = {
                messages: [...messages, { content: question, role: "user" }],
                context: {
                    overrides: {
                        prompt_template: promptTemplate.length === 0 ? undefined : promptTemplate,
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
                        suggest_followup_questions: useSuggestFollowupQuestions,
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
                session_state: answers.length ? answers[answers.length - 1][1].session_state : null
            };

            const response = await chatApi(request, shouldStream, token);
            if (!response.body) {
                throw Error("No response body");
            }
            if (response.status > 299 || !response.ok) {
                throw Error(`Request failed with status ${response.status}`);
            }
            if (shouldStream) {
                const parsedResponse: ChatAppResponse = await handleAsyncRequest(question, answers, response.body);
                setAnswers([...answers, [question, parsedResponse]]);
                if (typeof parsedResponse.session_state === "string" && parsedResponse.session_state !== "") {
                    const token = client ? await getToken(client) : undefined;
                    historyManager.addItem(parsedResponse.session_state, [...answers, [question, parsedResponse]], token);
                }
            } else {
                const parsedResponse: ChatAppResponseOrError = await response.json();
                if (parsedResponse.error) {
                    throw Error(parsedResponse.error);
                }
                setAnswers([...answers, [question, parsedResponse as ChatAppResponse]]);
                if (typeof parsedResponse.session_state === "string" && parsedResponse.session_state !== "") {
                    const token = client ? await getToken(client) : undefined;
                    historyManager.addItem(parsedResponse.session_state, [...answers, [question, parsedResponse as ChatAppResponse]], token);
                }
            }
            setSpeechUrls([...speechUrls, null]);
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswers([]);
        setSpeechUrls([]);
        setStreamedAnswers([]);
        setIsLoading(false);
        setIsStreaming(false);
    };

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [isLoading]);
    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "auto" }), [streamedAnswers]);
    useEffect(() => {
        getConfig();
    }, []);

    const handleSettingsChange = (field: string, value: any) => {
        switch (field) {
            case "promptTemplate":
                setPromptTemplate(value);
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
            case "useQueryRewriting":
                setUseQueryRewriting(value);
                break;
            case "reasoningEffort":
                setReasoningEffort(value);
                break;
            case "useSemanticCaptions":
                setUseSemanticCaptions(value);
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
            case "shouldStream":
                setShouldStream(value);
                break;
            case "useSuggestFollowupQuestions":
                setUseSuggestFollowupQuestions(value);
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
    };

    const [enableCitationTab, setEnableCitationTab] = useState(false);

    const onShowCitation = (citation: string, index: number, citationContent?: string) => {
        // Prevent rapid clicking by adding a small debounce
        if (isLoading || isStreaming) return;

        console.log("onShowCitation called with:", { citation, citationContent: citationContent ? "content provided" : "no content" });

        // CUSTOM: Check if citation is blocked from iframe embedding
        if (isIframeBlocked(citation)) {
            window.open(citation, "_blank", "noopener,noreferrer");
            return;
        }

        // Use the citation directly as received
        setActiveCitation(citation);

        // If citationContent is provided, use it; otherwise it will be found in SupportingContent
        setActiveCitationContent(citationContent || "");
        setActiveCitationLabel(citation); // Use the citation directly
        setActiveAnalysisPanelTab(AnalysisPanelTabs.SupportingContentTab);
        setEnableCitationTab(false);
        setSelectedAnswer(index);
    };

    const onToggleTab = (tab: AnalysisPanelTabs, index: number) => {
        if (activeAnalysisPanelTab === tab && selectedAnswer === index) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            // Enable citation tab when explicitly requested
            if (tab === AnalysisPanelTabs.CitationTab) {
                setEnableCitationTab(true);
            }
            setActiveAnalysisPanelTab(tab);
        }

        setSelectedAnswer(index);
    };

    const { t, i18n } = useTranslation();

    // Load categories for dropdown (ensure options are strings, not objects)
    const { categories = [], loading: categoriesLoading } = useCategories();

    const categoryOptions: IDropdownOption[] = [
        { key: "", text: "All Categories" },
        // Ensure each option is a simple { key: string, text: string }
        ...categories.filter(c => typeof c?.key === "string" && typeof c?.text === "string" && c.key !== "").map(c => ({ key: c.key, text: c.text }))
    ];

    // Selected keys from CSV
    const includeKeys = includeCategory
        ? includeCategory
              .split(",")
              .map(s => s.trim())
              .filter(Boolean)
        : [];

    const onIncludeCategoryChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IDropdownOption) => {
        if (!option) return;
        const key = String(option.key || "");

        // Selecting "All" toggles the checkmark and clears specific selections
        if (key === "") {
            setAllCategoriesSelected(!!option.selected);
            setIncludeCategory(""); // keep backend filter as "no filter"
            setUserHasInteracted(true);
            setUserTriedToSearch(false);
            return;
        }

        // Selecting any specific category clears "All"
        setAllCategoriesSelected(false);

        let next = includeKeys.slice();
        if (option.selected) {
            if (!next.includes(key)) next.push(key);
        } else {
            next = next.filter(k => k !== key);
        }

        const newValue = next.join(",");
        setIncludeCategory(newValue);
        setUserHasInteracted(true);
        setUserTriedToSearch(false);

        // If user deselects all categories (empty selection), require new interaction
        if (newValue === "" && !allCategoriesSelected) {
            setUserHasInteracted(false);
        }
    };

    return (
        <div className={styles.container}>
            {/* Setting the page title using react-helmet-async */}
            <Helmet>
                <title>{t("pageTitle")}</title>
            </Helmet>
            <div className={styles.commandsSplitContainer}>
                <div className={styles.commandsContainer}>
                    {((useLogin && showChatHistoryCosmos) || showChatHistoryBrowser) && (
                        <HistoryButton className={styles.commandButton} onClick={() => setIsHistoryPanelOpen(!isHistoryPanelOpen)} />
                    )}
                </div>
                <div className={styles.commandsContainer}>
                    <ClearChatButton className={styles.commandButton} onClick={clearChat} disabled={!lastQuestionRef.current || isLoading} />
                    {showUserUpload && <UploadFile className={styles.commandButton} disabled={!loggedIn} />}
                    <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                </div>
            </div>
            <div className={styles.chatRoot} style={{ marginLeft: isHistoryPanelOpen ? "300px" : "0" }}>
                <div className={styles.chatContainer}>
                    {!lastQuestionRef.current ? (
                        <div className={styles.chatEmptyState}>
                            <img src={appLogo} alt="App logo" width="120" height="120" />

                            <h1 className={styles.chatEmptyStateTitle}>{t("chatEmptyStateTitle")}</h1>
                            <h2 className={styles.chatEmptyStateSubtitle}>{t("chatEmptyStateSubtitle")}</h2>
                            {showLanguagePicker && <LanguagePicker onLanguageChange={newLang => i18n.changeLanguage(newLang)} />}

                            <ExampleList onExampleClicked={onExampleClicked} useGPT4V={useGPT4V} />
                        </div>
                    ) : (
                        <div className={styles.chatMessageStream}>
                            {isStreaming &&
                                streamedAnswers.map((streamedAnswer, index) => {
                                    // Build conversation history up to this point for feedback
                                    const conversationHistory = streamedAnswers.slice(0, index + 1).flatMap(([q, a]) => [
                                        { role: "user" as const, content: q },
                                        { role: "assistant" as const, content: a.message?.content || "" }
                                    ]);
                                    return (
                                        <div key={index}>
                                            <UserChatMessage message={streamedAnswer[0]} />
                                            <div className={styles.chatMessageGpt}>
                                                <Answer
                                                    isStreaming={true}
                                                    key={index}
                                                    answer={streamedAnswer[1]}
                                                    index={index}
                                                    speechConfig={speechConfig}
                                                    isSelected={false}
                                                    onCitationClicked={(c, citationContent) => onShowCitation(c, index, citationContent)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab, index)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab, index)}
                                                    onFollowupQuestionClicked={q => makeApiRequest(q)}
                                                    showFollowupQuestions={useSuggestFollowupQuestions && answers.length - 1 === index}
                                                    showSpeechOutputAzure={showSpeechOutputAzure}
                                                    showSpeechOutputBrowser={showSpeechOutputBrowser}
                                                    userPrompt={streamedAnswer[0]}
                                                    conversationHistory={conversationHistory}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            {!isStreaming &&
                                answers.map((answer, index) => {
                                    // Build conversation history up to this point for feedback
                                    const conversationHistory = answers.slice(0, index + 1).flatMap(([q, a]) => [
                                        { role: "user" as const, content: q },
                                        { role: "assistant" as const, content: a.message?.content || "" }
                                    ]);
                                    return (
                                        <div key={index}>
                                            <UserChatMessage message={answer[0]} />
                                            <div className={styles.chatMessageGpt}>
                                                <Answer
                                                    isStreaming={false}
                                                    key={index}
                                                    answer={answer[1]}
                                                    index={index}
                                                    speechConfig={speechConfig}
                                                    isSelected={selectedAnswer === index && activeAnalysisPanelTab !== undefined}
                                                    onCitationClicked={(c, citationContent) => onShowCitation(c, index, citationContent)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab, index)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab, index)}
                                                    onFollowupQuestionClicked={q => makeApiRequest(q)}
                                                    showFollowupQuestions={useSuggestFollowupQuestions && answers.length - 1 === index}
                                                    showSpeechOutputAzure={showSpeechOutputAzure}
                                                    showSpeechOutputBrowser={showSpeechOutputBrowser}
                                                    userPrompt={answer[0]}
                                                    conversationHistory={conversationHistory}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            {isLoading && (
                                <>
                                    <UserChatMessage message={lastQuestionRef.current} />
                                    <div className={styles.chatMessageGptMinWidth}>
                                        <AnswerLoading />
                                    </div>
                                </>
                            )}
                            {error ? (
                                <>
                                    <UserChatMessage message={lastQuestionRef.current} />
                                    <div className={styles.chatMessageGptMinWidth}>
                                        <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                                    </div>
                                </>
                            ) : null}
                            <div ref={chatMessageStreamEnd} />
                        </div>
                    )}

                    <div className={styles.chatInput}>
                        <QuestionInput
                            clearOnSend={false}
                            placeholder={t("defaultExamples.placeholder")}
                            disabled={isLoading}
                            onSend={question => makeApiRequest(question)}
                            showSpeechInput={showSpeechInput}
                            leftOfSend={
                                showCategoryFilter || (showAgenticRetrievalOption && useAgenticRetrieval) ? (
                                    <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                                        {showCategoryFilter && (
                                            <Dropdown
                                                multiSelect
                                                styles={{
                                                    dropdown: { minWidth: 140, maxWidth: 180 },
                                                    title: { fontSize: "13px", height: "32px", lineHeight: "30px", padding: "0 28px 0 8px" },
                                                    caretDownWrapper: { height: "32px", lineHeight: "30px" },
                                                    callout: { minWidth: 300, maxWidth: 400 },
                                                    dropdownItem: { minHeight: "32px", height: "auto", padding: "6px 8px", fontSize: "13px" },
                                                    dropdownOptionText: { whiteSpace: "normal", fontSize: "13px", lineHeight: "18px" }
                                                }}
                                                options={categoryOptions}
                                                selectedKeys={allCategoriesSelected ? [""] : includeKeys}
                                                onChange={onIncludeCategoryChange}
                                                onRenderTitle={(items?: IDropdownOption[]) => {
                                                    if (!items || items.length === 0) return <span>Category</span>;
                                                    if (items.some(i => i.key === "")) return <span>All</span>;
                                                    if (items.length === 1) return <span title={items[0].text}>{items[0].text}</span>;
                                                    return <span title={items.map(i => i.text).join(", ")}>{items.length} selected</span>;
                                                }}
                                                disabled={isLoading || categoriesLoading}
                                                placeholder="Category"
                                            />
                                        )}
                                        {/* CUSTOM: Search Depth dropdown for agentic retrieval reasoning effort.
                                            This allows users to control how thoroughly the system plans search queries.
                                            Integration point - re-add after upstream merges. */}
                                        {showAgenticRetrievalOption && useAgenticRetrieval && (
                                            <Dropdown
                                                styles={{
                                                    dropdown: { minWidth: 90, maxWidth: 110 },
                                                    title: { fontSize: "13px", height: "32px", lineHeight: "30px", padding: "0 24px 0 8px" },
                                                    caretDownWrapper: { height: "32px", lineHeight: "30px" },
                                                    dropdownItem: { padding: "8px 12px" },
                                                    dropdownItemSelected: { padding: "8px 12px" }
                                                }}
                                                options={[
                                                    {
                                                        key: "minimal",
                                                        text: t("labels.agenticReasoningEffortOptions.minimal"),
                                                        data: { description: "Fast single search. Best for straightforward questions like 'What is CPR Part 31?'" }
                                                    },
                                                    {
                                                        key: "low",
                                                        text: t("labels.agenticReasoningEffortOptions.low"),
                                                        data: { description: "Balanced search depth. Recommended for most legal questions." }
                                                    },
                                                    {
                                                        key: "medium",
                                                        text: t("labels.agenticReasoningEffortOptions.medium"),
                                                        data: { description: "Comprehensive multi-source search. Best for complex analysis or questions spanning multiple rules." }
                                                    }
                                                ]}
                                                selectedKey={reasoningEffort}
                                                onChange={(_ev, option) => setReasoningEffort((option?.key as string) || "low")}
                                                onRenderTitle={(items?: IDropdownOption[]) => {
                                                    if (!items || items.length === 0) return <span>Depth</span>;
                                                    return <span>{items[0].text}</span>;
                                                }}
                                                onRenderOption={(option?: IDropdownOption) => {
                                                    if (!option) return null;
                                                    return (
                                                        <div style={{ display: "flex", alignItems: "flex-start", gap: "8px", width: "100%" }}>
                                                            <div style={{ flex: 1 }}>
                                                                <div style={{ fontWeight: 600, fontSize: "13px" }}>{option.text}</div>
                                                                <div style={{ fontSize: "11px", color: "#666", marginTop: "2px", lineHeight: "1.3" }}>
                                                                    {option.data?.description}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                }}
                                                disabled={isLoading}
                                                placeholder="Depth"
                                                calloutProps={{ styles: { root: { minWidth: 280 } } }}
                                            />
                                        )}
                                    </div>
                                ) : undefined
                            }
                        />
                        {showCategoryFilter && userTriedToSearch && !userHasInteracted && (
                            <div className={styles.categoryWarning}>
                                Please select a category before searching. Choose "All Categories" to search all documents.
                            </div>
                        )}
                    </div>
                </div>

                {answers.length > 0 && activeAnalysisPanelTab && (
                    <AnalysisPanel
                        className={styles.chatAnalysisPanel}
                        activeCitation={activeCitation}
                        onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                        citationHeight="600px"
                        answer={answers[selectedAnswer][1]}
                        activeTab={activeAnalysisPanelTab}
                        activeCitationLabel={activeCitationLabel}
                        activeCitationContent={activeCitationContent}
                        enableCitationTab={enableCitationTab}
                        onCitationChanged={citation => {
                            setActiveCitation(citation);
                            setEnableCitationTab(true);
                        }}
                    />
                )}

                {((useLogin && showChatHistoryCosmos) || showChatHistoryBrowser) && (
                    <HistoryPanel
                        provider={historyProvider}
                        isOpen={isHistoryPanelOpen}
                        notify={!isStreaming && !isLoading}
                        onClose={() => setIsHistoryPanelOpen(false)}
                        onChatSelected={answers => {
                            if (answers.length === 0) return;
                            setAnswers(answers);
                            lastQuestionRef.current = answers[answers.length - 1][0];
                        }}
                    />
                )}

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
                        shouldStream={shouldStream}
                        streamingEnabled={streamingEnabled}
                        useSuggestFollowupQuestions={useSuggestFollowupQuestions}
                        showSuggestFollowupQuestions={true}
                        showAgenticRetrievalOption={showAgenticRetrievalOption}
                        useAgenticRetrieval={useAgenticRetrieval}
                        onChange={handleSettingsChange}
                    />
                    {useLogin && <TokenClaimsDisplay />}
                </Panel>

                {/* CUSTOM: Data Privacy Notice for lawyers testing the system */}
                <DataPrivacyNotice showBanner={true} />
            </div>
        </div>
    );
};

export default Chat;
