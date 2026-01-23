import ReactMarkdown from "react-markdown";

export const Report = ({ llmAnswer }) => {
    return (
        <div className="select-elements">
            <h1>Identified Threats</h1>
            <div className="report">
                In the part below each threat found by the Insider Treat Modeler
                with its potential process elements, impact, and mitigation
                strategies are listed.
            </div>
            <div className="spacer" />
            <div className="report">
                {llmAnswer ? (
                    <ReactMarkdown>{llmAnswer}</ReactMarkdown>
                ) : (
                    <p>No LLM answer provided.</p>
                )}
            </div>
        </div>
    );
};
