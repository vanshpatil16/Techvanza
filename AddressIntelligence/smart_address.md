# System Architecture - Smart Address Intelligence Engine

```mermaid
graph LR
    %% ==========================================
    %% 🎨 COLOR PALETTE & STYLES
    %% ==========================================
    
    %% NLP (Light Blue)
    classDef nlp fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,rx:5,ry:5,color:#000
    
    %% Geocoding (Green)
    classDef geo fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,rx:5,ry:5,color:#000
    
    %% Historical/ML (Orange)
    classDef ml fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,rx:5,ry:5,color:#000
    
    %% Output (Grey)
    classDef output fill:#f5f5f5,stroke:#616161,stroke-width:2px,rx:5,ry:5,color:#000
    
    %% User Input (White/Dashed)
    classDef input fill:#ffffff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5,rx:5,ry:5,color:#000

    %% ==========================================
    %% 🧩 NODES & SUBGRAPHS
    %% ==========================================

    %% 1. User Input
    User([User Input<br/>Unstructured Address Text]):::input

    %% 2. NLP Pipeline
    subgraph NLP_Pipeline [Landmark Extraction Pipeline (spaCy + Rule-based NLP)]
        direction TB
        L1[Extract Landmarks]:::nlp
        L2[Extract Spatial Relations<br/>(near/behind/opposite)]:::nlp
        L3[Extract Locality + Pincode]:::nlp
        Context[Context Builder<br/>Structured Metadata Output]:::nlp
    end

    %% 3. Geocoding Pipeline
    subgraph Geo_Pipeline [Geocoding Pipeline]
        direction TB
        G1[Multi-query Generation]:::geo
        G2[Nominatim Candidate Fetching]:::geo
        G3[Constraint-based Re-ranking<br/>• Pincode match weight<br/>• Locality match weight<br/>• Landmark match weight]:::geo
    end

    %% 4. Historical Matching Pipeline
    subgraph Hist_Pipeline [Historical Matching Pipeline (Fallback)]
        direction TB
        H1[TF-IDF Vectorization]:::ml
        H2[Cosine Similarity]:::ml
        H3[Top-K Retrieval]:::ml
        H4[Weighted Locality Voting]:::ml
    end

    %% 5. Output Modules
    Confidence[Confidence Scoring Module]:::output

    Final[Final Output<br/>-----------------<br/>Latitude<br/>Longitude<br/>Locality<br/>Pincode<br/>Confidence Score<br/>Explainability Trace]:::output

    %% ==========================================
    %% 🔗 DATA FLOW
    %% ==========================================

    %% Input -> NLP
    User ==> L1
    L1 --> L2
    L2 --> L3
    L3 --> Context

    %% NLP -> Geocoding (Primary)
    Context ==> G1
    
    %% NLP -> Historical (Fallback)
    Context -. Fallback .-> H1

    %% Geocoding Flow
    G1 --> G2
    G2 --> G3
    G3 --> Confidence

    %% Historical Flow
    H1 --> H2
    H2 --> H3
    H3 --> H4
    H4 --> Confidence

    %% Final Output
    Confidence ==> Final
```
