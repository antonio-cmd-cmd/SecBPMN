import json
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import JSONResponse, Response
from app.llm.qa_chain import build_qa_chain
from app.llm.query_builder import build_analysis_query
from app.utils.file_loader import load_knowledge_base
from app.utils.document_utils import extract_threat_docs
from app.llm.vectorstore import setup_vectorstore_lance
from app.config import KNOWLEDGE_BASE_PATH
import uvicorn
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.llm.response_processor import strip_bpmn_id_blocks
from app.llm.response_processor import extract_bpmn_id_suffixes
from app.utils.bpmn_validator import validate_bpmn
from app.llm.bpmn_mitigation_generator import generate_mitigated_bpmn

qa_chain = None  # Global variable for the QA chain


@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_chain
    # Load knowledge base and setup vectorstore
    kb_data = load_knowledge_base(KNOWLEDGE_BASE_PATH)
    docs = extract_threat_docs(kb_data)
    vs = setup_vectorstore_lance(docs)
    # Build the QA chain
    qa_chain = build_qa_chain(vs)
    print("QA chain setup complete.")

    # Test the setup with a file
    """ print("Testing setup with file...")
    try:
        with open("resources/testBusinessProcessSIMPLIFIED.bpmn", "r", encoding="utf-8") as file:
            bpmn = file.read()
        result = analyze_uploaded_xml(bpmn)
        print("Test result:", result)
    except Exception as e:
        print(f"Error during setup test: {e}") """
    yield  # Lifespan context

app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:3000",  # Explicit frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/validate-bpmn/")
async def validate_bpmn_endpoint(file: UploadFile = File(...)):
    """
    Validate a BPMN file by converting it to a Petri net and checking for soundness.
    
    Args:
        file: Uploaded BPMN file
        
    Returns:
        JSON response with validation result
    """
    try:
        xml_content = await file.read()
        xml_str = xml_content.decode("utf-8")
        
        # Validate the BPMN
        validation_result = validate_bpmn(xml_str)
        
        return JSONResponse(content=validation_result)
        
    except Exception as e:
        return JSONResponse(
            content={
                'valid': False,
                'message': f'Error processing file: {str(e)}',
                'error_type': 'processing_error'
            },
            status_code=400
        )

@app.post("/analyze-xml/")
async def analyze_xml(
    file: UploadFile = File(...),
    principles: str = Form(...),
    context: str = Form(...)
):
    # Parse JSON strings
    principles_list = json.loads(principles)
    context_data = json.loads(context)
    xml_content = await file.read()
    print("Principles:", principles_list)
    print("Context:", context_data)

    prompt = build_analysis_query(xml_content.decode("utf-8"), context_data, principles_list)

    print("DEBUG analyze_xml prompt:", prompt)

    if qa_chain is None:
        raise RuntimeError("QA Chain is not initialized yet!")
    result = qa_chain.invoke({"query": prompt})
    element_ids = extract_bpmn_id_suffixes(result['result'])
    markdown = strip_bpmn_id_blocks(result['result'])

    print("DEBUG analyze_xml result:", result['result'])
    print("DEBUG ELEMENT IDs result:", element_ids)
    return JSONResponse(content={"doc": markdown, "element_ids": element_ids})


@app.post("/generate-mitigated-bpmn/")
async def generate_mitigated_bpmn_endpoint(
    file: UploadFile = File(...),
    principles: str = Form(...),
    context: str = Form(...),
    threat_analysis: str = Form(...)
):
    """
    Generate a mitigated BPMN based on threat analysis.
    
    Args:
        file: Original BPMN file
        principles: JSON string of security principles
        context: JSON string of process context
        threat_analysis: Threat analysis markdown from previous step
        
    Returns:
        JSON response with mitigated BPMN XML
    """
    try:
        # Parse inputs
        print("=== GENERATE MITIGATED BPMN DEBUG ===")
        print(f"Received file: {file.filename}")
        
        principles_list = json.loads(principles)
        context_data = json.loads(context)
        xml_content = await file.read()
        original_bpmn = xml_content.decode("utf-8")
        
        print(f"Principles: {principles_list}")
        print(f"Context: {context_data}")
        print(f"Threat analysis length: {len(threat_analysis)}")
        print(f"Original BPMN length: {len(original_bpmn)}")
        
        print("Generating mitigated BPMN...")
        print("Principles:", principles_list)
        print("Context:", context_data)
        
        if qa_chain is None:
            raise RuntimeError("QA Chain is not initialized yet!")
        
        # Generate mitigated BPMN
        result = generate_mitigated_bpmn(
            original_bpmn,
            threat_analysis,
            context_data,
            principles_list,
            qa_chain
        )
        
        if result['success']:
            return JSONResponse(content={
                "success": True,
                "message": result['message'],
                "mitigated_bpmn": result['mitigated_bpmn'],
                "element_count": result.get('element_count', 0)
            })
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": result['message']
                },
                status_code=400
            )
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JSONResponse(
            content={
                "success": False,
                "message": f"Invalid JSON in request: {str(e)}"
            },
            status_code=400
        )
    except Exception as e:
        print(f"Error generating mitigated BPMN: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={
                "success": False,
                "message": f"Error: {str(e)}"
            },
            status_code=500
        )


@app.post("/download-bpmn/")
async def download_bpmn(bpmn_xml: str = Form(...)):
    """
    Download BPMN file.
    
    Args:
        bpmn_xml: BPMN XML content as string
        
    Returns:
        BPMN file as downloadable response
    """
    try:
        # Return as downloadable file
        return Response(
            content=bpmn_xml.encode('utf-8'),
            media_type='application/xml',
            headers={
                'Content-Disposition': 'attachment; filename="mitigated_process.bpmn"'
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error creating download: {str(e)}"},
            status_code=500
        )
    

def start_api():
    uvicorn.run("app.api.routes:app", host="0.0.0.0", port=8000, reload=True)
