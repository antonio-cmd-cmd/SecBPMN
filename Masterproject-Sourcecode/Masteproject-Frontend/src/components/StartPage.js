import "../App.css";
import methodology from "../resources/methodology.png";

function StartPage({ onNext }) {
    return (
        <div className="centered-page">
            <div style={{ width: "1000px", textAlign: "center" }}>
                <h1>Welcome to the Insider Threat Modeler 2.0</h1>
                <div>
                    This tool helps you to analyze business processes for
                    potential insider threats. It is supported by a rertieval
                    augmented generation architecture to provide tailored
                    threats to the security goals and context of your business
                    process.
                </div>
                <div className="spacer" />
                <div>
                    Please follow the steps described below to analyze your
                    business process:
                </div>
                <div className="spacer" />
                <img
                    src={methodology}
                    alt="Insider Threat Modeler Logo"
                    style={{ width: "800px", marginBottom: "20px" }}
                />
                <div className="spacer" />
                <button
                    className="submit"
                    onClick={onNext}
                    style={{ marginLeft: 16 }}
                >
                    Start
                </button>
            </div>
        </div>
    );
}

export default StartPage;
