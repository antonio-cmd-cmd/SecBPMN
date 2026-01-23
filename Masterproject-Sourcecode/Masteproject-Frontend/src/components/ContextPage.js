import "../App.css";

function ContextPage({ context, setContext, onNext, onBack }) {
    //This function was written with the help of ChatGPT.
    const handleChange = (key) => (e) =>
        setContext({ ...context, [key]: e.target.value });

    const renderQuestion = (label, key, placeholder, rows = 2) => (
        <div className="context-question" key={key}>
            <label>
                <strong>{label}</strong>
                <textarea
                    className="context-textarea"
                    rows={rows}
                    value={context[key] || ""}
                    onChange={handleChange(key)}
                    placeholder={placeholder}
                />
            </label>
        </div>
    );

    return (
        <div className="centered-page">
            <h1>Process Context</h1>
            <div>
                Please answer the following questions to provide the prototype
                more context for the process you are analyzing.
            </div>
            <div className="context-form">
                {renderQuestion(
                    "1.How would you explain the BPMN process, including the main steps and their purpose?",
                    "processQuestion",
                    "Describe the purpose or intent and important steps.",
                    3
                )}
                {renderQuestion(
                    "2. What systems or technologies are involved?",
                    "systemQuestion",
                    "List IT systems, applications, platforms, authentication etc."
                )}
                {renderQuestion(
                    "3. Who are the primary roles or actors?",
                    "roleQuestion",
                    "E.g., users, admins, external partners."
                )}
                {renderQuestion(
                    "4. Other notes, risks, or special considerations?",
                    "otherQuestion",
                    "Describe any other relevant context. E.g. high security assets, sensitive data"
                )}
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        width: "100%",
                        marginTop: "32px",
                    }}
                >
                    <button className="context-back-button" onClick={onBack}>
                        Back
                    </button>
                    <button
                        className="submit"
                        onClick={onNext}
                        style={{ marginLeft: 16 }}
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ContextPage;
