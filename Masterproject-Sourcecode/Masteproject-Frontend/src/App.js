import { useState } from "react";
import BpmnModelViewer from "./components/BpmnModelViewer";
import "bpmn-js/dist/assets/diagram-js.css";
import "bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css";
import "./App.css";
import ErrorBoundary from "./ErrorBoundary";
import { SecurityPrinciples } from "./models/securityPrinciples";
import ContextPage from "./components/ContextPage";
import StartPage from "./components/StartPage";
import { Tooltip } from "react-tooltip";

function BPMNUploadPage({ onUpload, onBack, validationError, isValidating }) {
    return (
        <div>
            <h1>BPMN Upload</h1>
            <div>
                Upload your BPMN file to analyze the process. Ensure it is in
                BPMN 2.0 format.
            </div>
            {validationError && (
                <div style={{
                    marginTop: '20px',
                    padding: '15px',
                    backgroundColor: '#ffebee',
                    border: '1px solid #ef5350',
                    borderRadius: '4px',
                    color: '#c62828'
                }}>
                    <strong>Validation Error:</strong>
                    <p>{validationError}</p>
                </div>
            )}
            {isValidating && (
                <div style={{
                    marginTop: '20px',
                    padding: '15px',
                    backgroundColor: '#e3f2fd',
                    border: '1px solid #2196f3',
                    borderRadius: '4px',
                    color: '#1565c0'
                }}>
                    <strong>Validating BPMN...</strong>
                    <p>Please wait while we verify your BPMN model.</p>
                </div>
            )}
            <div className="spacer" />
            <input
                id="bpmn-upload"
                type="file"
                accept=".bpmn"
                onChange={onUpload}
                style={{ display: "none" }}
                disabled={isValidating}
            />
            <label 
                htmlFor="bpmn-upload" 
                className={`button upload-button ${isValidating ? 'disabled' : ''}`}
                style={{ opacity: isValidating ? 0.5 : 1, cursor: isValidating ? 'not-allowed' : 'pointer' }}
            >
                {isValidating ? 'Validating...' : 'Select BPMN File'}
            </label>
            <div style={{ marginTop: 24 }}>
                <button className="back-middle" onClick={onBack} disabled={isValidating}>
                    Back
                </button>
            </div>
        </div>
    );
}

function App() {
    const [step, setStep] = useState(0); // 0: startpage, 1: principles, 2: context, 3: bpmn, 4: report
    const [principlesState, setPrinciplesState] = useState({
        confidentiality: false,
        integrity: false,
        availability: false,
        accountability: false,
        authenticity: false,
    });
    const [selectedPrinciples, setSelectedPrinciples] = useState([]);
    const [context, setContext] = useState({
        processQuestion: "",
        systemQuestion: "",
        roleQuestion: "",
        otherQuestion: "",
    });
    const [bpmnXml, setBpmnXml] = useState("");
    const [validationError, setValidationError] = useState("");
    const [isValidating, setIsValidating] = useState(false);

    // Principle logic as before
    const togglePrinciple = (principle) => {
        setPrinciplesState((prevState) => ({
            ...prevState,
            [principle]: !prevState[principle],
        }));
    };

    const handlePrinciplesSubmit = () => {
        const updatedPrinciples = Object.keys(principlesState)
            .filter((key) => principlesState[key])
            .map((key) => SecurityPrinciples[key]);

        setSelectedPrinciples(updatedPrinciples);
        setStep(2); // Move to context page
    };

    const handleContextNext = () => setStep(3); // Move to BPMN upload
    const handleContextBack = () => setStep(1); // Back to principles

    const validateBpmnFile = async (xmlContent) => {
        setIsValidating(true);
        setValidationError("");
        
        try {
            // Create a FormData object to send the file
            const formData = new FormData();
            const blob = new Blob([xmlContent], { type: 'application/xml' });
            formData.append('file', blob, 'model.bpmn');
            
            // Call the validation endpoint
            const response = await fetch('http://localhost:8000/validate-bpmn/', {
                method: 'POST',
                body: formData,
            });
            
            const result = await response.json();
            
            if (result.valid) {
                // Validation successful
                return true;
            } else {
                // Validation failed
                setValidationError(result.message || "BPMN validation failed");
                return false;
            }
        } catch (error) {
            setValidationError(`Error validating BPMN: ${error.message}`);
            return false;
        } finally {
            setIsValidating(false);
        }
    };

    const handleBpmnUpload = async (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = async (event) => {
                const xmlContent = event.target.result;
                
                // Validate the BPMN before proceeding
                const isValid = await validateBpmnFile(xmlContent);
                
                if (isValid) {
                    setBpmnXml(xmlContent); // Save the XML as a string
                    setStep(4); // Move to report
                    console.log("BPMN file uploaded and validated:", file.name);
                    console.log("Context", context);
                    console.log("Principles", selectedPrinciples);
                } else {
                    // Validation failed, error message is already set
                    console.log("BPMN validation failed");
                }
            };
            reader.readAsText(file); // Read as text
        }
    };
    const handleBpmnBack = () => setStep(2); // Back to context

    const principleTooltips = {
        confidentiality:
            "Prevents unauthorized access to sensitive or confidential data.",
        integrity:
            "Ensures data and system accuracy by preventing unauthorized modification.",
        availability:
            "Ensures systems and data are accessible when needed by authorized users.",
        accountability:
            "Tracks user actions to ensure responsible behavior and traceability.",
        authenticity:
            "Verifies the identity of users and systems to prevent impersonation or forgery.",
    };

    function getTooltipText(principleKey) {
        return principleTooltips[principleKey] || "No description available.";
    }

    // PRINCIPLES PAGE
    const renderPrincipleButton = (principleKey) => (
        <>
            <button
                key={principleKey}
                style={{
                    backgroundColor: principlesState[principleKey]
                        ? "#709eff"
                        : null,
                    fontWeight: principlesState[principleKey] ? 700 : 400,
                    margin: "8px",
                }}
                onClick={() => togglePrinciple(principleKey)}
                data-tooltip-id={`tip-${principleKey}`}
                data-tooltip-content={getTooltipText(principleKey)}
            >
                {SecurityPrinciples[principleKey]}
            </button>
            <Tooltip id={`tip-${principleKey}`} place="right" effect="solid">
                {getTooltipText(principleKey)}
            </Tooltip>
        </>
    );

    return (
        <div className="App">
            <header className="App-header">
                <h1>Insider Threat Modeler in BPMN 2.0</h1>
            </header>
            {step === 0 && <StartPage onNext={() => setStep(1)} />}
            {step === 1 && (
                <div className="text centered-page">
                    <h1>Security Principle Selection</h1>
                    <div>
                        Please select the security principles that are the most
                        important for your process.
                    </div>
                    <div className="spacer" />
                    <div className="select-box">
                        <div className="flex-column">
                            {Object.keys(principlesState).map(
                                renderPrincipleButton
                            )}
                        </div>
                    </div>
                    <div className="spacer" />

                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            width: "50%",
                            marginTop: "32px",
                        }}
                    >
                        <button
                            className="context-back-button"
                            onClick={() => setStep(0)}
                        >
                            Back
                        </button>
                        <button
                            className="submit"
                            onClick={handlePrinciplesSubmit}
                            style={{ marginLeft: 16 }}
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
            {step === 2 && (
                <ContextPage
                    context={context}
                    setContext={setContext}
                    onNext={handleContextNext}
                    onBack={handleContextBack}
                />
            )}
            {step === 3 && (
                <BPMNUploadPage
                    onUpload={handleBpmnUpload}
                    onBack={handleBpmnBack}
                    validationError={validationError}
                    isValidating={isValidating}
                />
            )}
            {step === 4 && selectedPrinciples.length > 0 && bpmnXml && (
                <ErrorBoundary>
                    <BpmnModelViewer
                        selectedPrinciples={selectedPrinciples}
                        context={context}
                        bpmnXml={bpmnXml}
                        onBack={() => setStep(3)} //back to BPMN upload
                    />
                </ErrorBoundary>
            )}
        </div>
    );
}

export default App;
