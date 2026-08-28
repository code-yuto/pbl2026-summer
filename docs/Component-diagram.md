flowchart TD
    subgraph Team1["Hardware Team (Sensors & Circuit)"]
        S1[Soil moisture sensor]
        S2[Water level sensor]
    end

    subgraph Team2["Edge Software Team (Arduino Code)"]
        MCU[Microcontroller\nThreshold check]
        SendAlert[Send alert immediately]
        SendData[Send data\nJSON to server]
    end

    subgraph Team3["Backend Team (LLM & API)"]
        W_API[Weather API]
        LLM[LLM: contextual check]
        Flag[Flag as contextual anomaly]
        Report[Generate normal report]
        Notify[Notify user\nApp / LINE / Discord]
    end

    %% Connections
    S1 --> MCU
    S2 --> MCU
    
    MCU -- Anomaly --> SendAlert
    MCU -- Normal --> SendData
    
    SendAlert -.-> Notify
    
    SendData --> W_API
    W_API --> LLM
    
    LLM -- Inconsistent --> Flag
    LLM -- Consistent --> Report
    
    Flag -.-> Notify
    Report -.-> Notify
    
    %% Styling
    classDef anomaly fill:#fce4e4,stroke:#cc0000,stroke-width:1px;
    classDef normal fill:#e4fce4,stroke:#006600,stroke-width:1px;
    classDef mcu fill:#e4e4fc,stroke:#0000cc,stroke-width:1px;
    classDef api fill:#fcecd4,stroke:#cc6600,stroke-width:1px;
    
    class SendAlert,Flag anomaly;
    class Report normal;
    class MCU mcu;
    class W_API api;
