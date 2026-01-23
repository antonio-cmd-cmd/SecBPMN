import { useCallback, useEffect, useRef, useState } from "react";
import BpmnModeler from "bpmn-js/lib/Modeler";
import { Report } from "./Report";
import newDiagramPath from "../resources/newDiagram.bpmn";
import { usePDF } from "react-to-pdf";

const BpmnModelViewer = ({ selectedPrinciples, context, bpmnXml, onBack }) => {
    const canvas = document.getElementById("js-canvas");
    const modelerRef = useRef(null);

    const [isDiagramLoaded, setDiagramLoaded] = useState(false);
    const [reportShown, setReportShown] = useState(false);
    const [downloadBPMNLink, setDownloadBPMNLink] = useState("");
    const [svgLink, setSvgLink] = useState("");
    const [svgDiagram, setSvgDiagram] = useState(null);

    const [llmAnswer, setLlmAnswer] = useState("");
    const [loading, setLoading] = useState(false);
    const [mitigatedBpmn, setMitigatedBpmn] = useState("");
    const [generatingMitigation, setGeneratingMitigation] = useState(false);

    //PDF is generated from the report component
    const { toPDF, loadingPDF, error, targetRef } = usePDF({
        filename: "insider-threat-report.pdf",
        options: {
            format: "letter",
            orientation: "portrait",
            margin: 10,
        },
    });

    const handleDragOver = useCallback((e) => {
        e.stopPropagation();
        e.preventDefault();
        e.dataTransfer.dropEffect = "copy";
    }, []);

    const handleFileSelect = useCallback((e, callback, container) => {
        e.stopPropagation();
        e.preventDefault();

        const files = e.dataTransfer.files;
        const file = files[0];

        const reader = new FileReader();

        reader.onload = function (e) {
            const xml = e.target.result;
            callback(xml, container);
        };

        reader.readAsText(file);
    }, []);

    const openDiagram = useCallback(async (xml, container) => {
        try {
            await modelerRef.current.importXML(xml);

            container.classList.remove("with-error");
            container.classList.add("with-diagram");

            setDiagramLoaded(true);

            //Fit the viewport
            const canvas = modelerRef.current.get("canvas");
            canvas.zoom("fit-viewport");

            await modelerRef.current.saveXML(xml);
            await modelerRef.current.saveSVG();
        } catch (err) {
            container.classList.remove("with-diagram");
            container.classList.add("with-error");

            container.find(".error pre").text(err.message);

            console.error(err);
        }
    }, []);

    useEffect(() => {
        const container = document.getElementById("js-drop-zone");

        modelerRef.current = new BpmnModeler({
            container: canvas,
            keyboard: {
                bindTo: document,
            },
            //would help to get rid of sidebar
            additionalModules: [
                {
                    palette: ["value", {}],
                    paletteProvider: ["value", {}],
                },
            ],
        });

        // Needed to preload modeler to make drag & drop work -
        const loadDiagram = async () => {
            try {
                let xml;
                if (bpmnXml) {
                    xml = bpmnXml;
                } else {
                    const response = await fetch(newDiagramPath);
                    xml = await response.text();
                }
                await openDiagram(xml, container);
            } catch (err) {
                console.error(err);
            }
        };
        loadDiagram();

        container.addEventListener("dragover", (e) => handleDragOver(e), false);
        container.addEventListener(
            "drop",
            (e) => handleFileSelect(e, openDiagram, container),
            false
        );

        container.addEventListener(
            "drop",
            (e) => handleFileSelect(e, openDiagram, container),
            false
        );
    }, [canvas, handleDragOver, handleFileSelect, openDiagram, bpmnXml]);

    async function onShowThreats() {
        const elementRegistry = modelerRef.current.get("elementRegistry");

        setLoading(true);

        console.log("Elementregistry: ", elementRegistry);

        const formData = new FormData();
        const { xml } = await modelerRef.current.saveXML();
        formData.append("file", new Blob([xml], { type: "text/xml" }));
        // Append principles and context as JSON strings
        formData.append("principles", JSON.stringify(selectedPrinciples));
        formData.append("context", JSON.stringify(context));

        //send XML, principlres, and context to the backend
        try {
            const response = await fetch("http://localhost:8000/analyze-xml/", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Upload failed");
            }

            const result = await response.json();
            console.log("LLM Answer: ", result.doc);
            console.log("LLM Element IDs: ", result.element_ids);
            setLlmAnswer(result.doc);
            // get the element ids from the result and highlight them
            if (result.element_ids && result.element_ids.length > 0) {
                highlightBpmnElementsByIds(result.element_ids);
            }
        } catch (error) {
            console.log(error.message);
        }
        //change to report page
        setReportShown(true);
        setLoading(false);
    }

    const generateMitigatedBpmn = async () => {
        setGeneratingMitigation(true);
        try {
            console.log('=== GENERATING MITIGATED BPMN ===');
            const formData = new FormData();
            
            // Create a blob from the original BPMN XML
            const blob = new Blob([bpmnXml], { type: 'application/xml' });
            formData.append('file', blob, 'original.bpmn');
            formData.append('principles', JSON.stringify(selectedPrinciples));
            formData.append('context', JSON.stringify(context));
            formData.append('threat_analysis', llmAnswer);

            console.log('Sending request to backend...');
            console.log('Principles:', selectedPrinciples);
            console.log('Context:', context);
            console.log('Threat analysis length:', llmAnswer.length);

            const response = await fetch('http://localhost:8000/generate-mitigated-bpmn/', {
                method: 'POST',
                body: formData,
            });

            console.log('Response status:', response.status);
            
            const result = await response.json();
            console.log('Response data:', result);

            if (!response.ok) {
                throw new Error(result.message || 'Failed to generate mitigated BPMN');
            }
            
            if (result.success) {
                setMitigatedBpmn(result.mitigated_bpmn);
                console.log('Mitigated BPMN generated successfully');
                alert('Mitigated BPMN generated successfully! You can now download it.');
            } else {
                throw new Error(result.message || 'Failed to generate mitigated BPMN');
            }
        } catch (error) {
            console.error('Error generating mitigated BPMN:', error);
            alert(`Error: ${error.message}`);
        } finally {
            setGeneratingMitigation(false);
        }
    };

    const downloadMitigatedBpmn = async () => {
        if (!mitigatedBpmn) {
            alert('Please generate the mitigated BPMN first');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('bpmn_xml', mitigatedBpmn);

            const response = await fetch('http://localhost:8000/download-bpmn/', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to download BPMN');
            }

            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'mitigated_process.bpmn';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            console.log('Mitigated BPMN downloaded');
        } catch (error) {
            console.error('Error downloading mitigated BPMN:', error);
            alert(`Error: ${error.message}`);
        }
    };

    const highlightBpmnElementsByIds = (partialIds) => {
        //This function was written with the help of ChatGPT.

        const color = "#e03a23";
        //make sure that flows and lanes are not highlighted
        const allowedTypes = new Set([
            "bpmn:Task",
            "bpmn:UserTask",
            "bpmn:SendTask",
            "bpmn:ServiceTask",
            "bpmn:ManualTask",
            "bpmn:Activity",
            "bpmn:StartEvent",
            "bpmn:IntermediateCatchEvent",
            "bpmn:DataObjectReference",
            "bpmn:DataStoreReference",
            "bpmn:Gateway",
        ]);

        const elementRegistry = modelerRef.current.get("elementRegistry");
        const modeling = modelerRef.current.get("modeling");

        const allElements = Object.values(elementRegistry._elements).map(
            (e) => e.element
        );

        //only partialIds that are at the end of the element id, because the LLM returns false names
        const matchingElements = allElements.filter(
            (element) =>
                partialIds.some((partialId) =>
                    element.id.endsWith(partialId)
                ) && allowedTypes.has(element.type)
        );

        const foundIds = matchingElements.map((e) => e.id);
        const unfound = partialIds.filter(
            (partialId) =>
                !foundIds.some((fullId) => fullId.endsWith(partialId))
        );

        console.log("Matched elements:", matchingElements);
        if (unfound.length > 0) {
            console.warn("Unmatched partial IDs:", unfound);
        }
        // Highlight the matching elements in red
        if (matchingElements.length > 0) {
            modeling.setColor(matchingElements, { stroke: color });
        } else {
            console.warn("No allowed elements matched for highlight.");
        }

        //make diagram ready to download
        downloadBpmn();
        downloadSvg();
    };

    function setEncoded(data) {
        const encodedData = encodeURIComponent(data);

        if (data) {
            const href = `data:application/bpmn20-xml;charset=UTF-8,${encodedData}`;
            return href;
        } else {
            console.log("No data");
        }
    }

    const debounce = (fn, timeout) => {
        let timer;

        return function () {
            if (timer) {
                clearTimeout(timer);
            }

            timer = setTimeout(fn, timeout);
        };
    };

    const downloadBpmn = debounce(async () => {
        try {
            const { xml } = await modelerRef.current.saveXML({
                format: true,
            });
            const href = setEncoded(xml);
            if (href) {
                setDownloadBPMNLink(href);
                console.log("BPMN link set: ", href);
            }
        } catch (err) {
            console.error("Error happened saving XML: ", err);
            setEncoded(null);
        }
    }, 500);

    const downloadSvg = debounce(async () => {
        try {
            const { svg } = await modelerRef.current.saveSVG();
            setSvgDiagram(svg);
            const href = setEncoded(svg);
            if (href) {
                setSvgLink(href);
                console.log("SVG link set: ", href);
            }
        } catch (err) {
            console.error("Error happened saving svg: ", err);
            setEncoded(null);
        }
    }, 500);

    return (
        <div className="parent-container">
            <div className="content" id="js-drop-zone">
                <div className="message intro">
                    <div className="note">
                        Drop BPMN diagram from your desktop
                    </div>
                </div>
                <div className="message error">
                    <div className="note">
                        <p>Ooops, we could not display the BPMN 2.0 diagram.</p>
                        <div className="details">
                            <span>cause of the problem</span>
                            <pre></pre>
                        </div>
                    </div>
                </div>
                <div className="canvas" id="js-canvas"></div>
            </div>
            {reportShown ? (
                <>
                    <div ref={targetRef} className="report-wrapper">
                        <Report llmAnswer={llmAnswer} />
                    </div>
                    <ul className="buttons">
                        <li>download</li>
                        <li>
                            <a
                                id="js-download-diagram"
                                href={
                                    downloadBPMNLink ? downloadBPMNLink : null
                                }
                                download="insiderThreatDiagram.bpmn"
                                target="_blank"
                                rel="noreferrer"
                            >
                                BPMN diagram
                            </a>
                        </li>
                        <li>
                            <a
                                id="js-download-svg"
                                href={svgLink ? svgLink : null}
                                download="insiderThreatDiagram.svg"
                                target="_blank"
                                rel="noreferrer"
                            >
                                SVG image
                            </a>
                        </li>
                        <button
                            className="submit"
                            onClick={() => {
                                toPDF();
                            }}
                            disabled={loadingPDF}
                        >
                            {loadingPDF ? "Generating PDF" : "PDF report"}
                        </button>
                    </ul>
                    <div style={{
                        marginTop: '20px',
                        padding: '20px',
                        backgroundColor: '#f5f5f5',
                        borderRadius: '8px',
                        textAlign: 'center'
                    }}>
                        <h3 style={{ marginBottom: '15px' }}>Secure Your Process</h3>
                        <p style={{ marginBottom: '15px', color: '#666' }}>
                            Generate a mitigated BPMN with security controls applied
                        </p>
                        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                            <button
                                className="submit"
                                onClick={generateMitigatedBpmn}
                                disabled={generatingMitigation}
                                style={{
                                    backgroundColor: mitigatedBpmn ? '#4caf50' : '#709eff',
                                    opacity: generatingMitigation ? 0.6 : 1
                                }}
                            >
                                {generatingMitigation ? 'Generating...' : mitigatedBpmn ? '✓ Generated' : 'Generate Mitigated BPMN'}
                            </button>
                            {mitigatedBpmn && (
                                <button
                                    className="submit"
                                    onClick={downloadMitigatedBpmn}
                                    style={{ backgroundColor: '#2196f3' }}
                                >
                                    Download Mitigated BPMN
                                </button>
                            )}
                        </div>
                    </div>
                    {error && <p style={{ color: "red" }}>{error.message}</p>}
                </>
            ) : isDiagramLoaded && !loading ? (
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        width: "70%",
                        marginTop: "32px",
                        justifySelf: "center",
                    }}
                >
                    <button className="back-middle" onClick={onBack}>
                        Back
                    </button>
                    <button
                        className={"submit"}
                        onClick={() => onShowThreats()}
                    >
                        Show Threats
                    </button>
                </div>
            ) : (
                <div className="loading">
                    <div className="loader"></div>
                    <p>Analyzing BPMN diagram on insider threats...</p>
                </div>
            )}
        </div>
    );
};

export default BpmnModelViewer;
