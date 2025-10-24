# SPEC-132: Architecture Diagrams

Visual representations of gateway protocol architecture options.

---

## 🔍 CURRENT STATE

```mermaid
graph TB
    subgraph "Current Architecture - gRPC Only"
        Client[CLI/API Clients]
        Gateway[Gateway<br/>Port 13395<br/>gRPC-Only]

        GraphOps[GraphOps<br/>Port 13398<br/>gRPC ✅]
        Memory[Memory Service<br/>Port 13393<br/>REST]
        CoreAPI[Core API<br/>Port 13390<br/>REST]

        Client -->|gRPC| Gateway
        Gateway -->|gRPC ✅| GraphOps
        Gateway -.->|gRPC ❌| Memory
        Gateway -.->|gRPC ❌| CoreAPI

        Client -.->|Direct REST| Memory
        Client -.->|Direct REST| CoreAPI
    end

    style Gateway fill:#f9f,stroke:#333,stroke-width:2px
    style GraphOps fill:#9f9,stroke:#333,stroke-width:2px
    style Memory fill:#ff9,stroke:#333,stroke-width:2px
    style CoreAPI fill:#ff9,stroke:#333,stroke-width:2px
```

**Problem:** Gateway cannot route to REST backends, clients must access directly.

---

## 🎯 OPTION 1: gRPC-Only Gateway (Current)

```mermaid
graph TB
    subgraph "Option 1: gRPC-Only"
        Client1[gRPC Clients]
        Client2[REST Clients]
        Gateway1[Gateway<br/>13395<br/>gRPC-Only]

        GraphOps1[GraphOps<br/>13398<br/>gRPC]
        Memory1[Memory Service<br/>13393<br/>REST]
        CoreAPI1[Core API<br/>13390<br/>REST]

        Client1 -->|gRPC| Gateway1
        Gateway1 -->|gRPC| GraphOps1

        Client2 -->|REST Direct| Memory1
        Client2 -->|REST Direct| CoreAPI1
    end

    style Gateway1 fill:#9f9,stroke:#333,stroke-width:2px
    style GraphOps1 fill:#9f9,stroke:#333,stroke-width:2px
```

**Pros:** Simple, focused
**Cons:** No unified endpoint

---

## 🔄 OPTION 2: Hybrid Gateway (RECOMMENDED)

```mermaid
graph TB
    subgraph "Option 2: Hybrid Gateway with Translation"
        Client1[gRPC Clients]
        Client2[REST/JSON Clients]

        Gateway2[Gateway<br/>13395<br/>Hybrid Mode]

        subgraph "Gateway Internals"
            gRPCHandler[gRPC Handler]
            RESTHandler[REST Handler]
            Translator[Protocol Translator]
        end

        GraphOps2[GraphOps<br/>13398<br/>gRPC]
        Memory2[Memory Service<br/>13393<br/>REST]
        CoreAPI2[Core API<br/>13390<br/>REST]

        Client1 -->|gRPC| Gateway2
        Client2 -->|REST/JSON| Gateway2

        Gateway2 --> gRPCHandler
        Gateway2 --> RESTHandler

        gRPCHandler -->|gRPC native| GraphOps2
        RESTHandler -->|REST proxy| Memory2
        RESTHandler -->|REST proxy| CoreAPI2

        gRPCHandler -.->|via Translator| Memory2
        RESTHandler -.->|via Translator| GraphOps2
    end

    style Gateway2 fill:#9f9,stroke:#333,stroke-width:4px
    style Translator fill:#f9f,stroke:#333,stroke-width:2px
```

**Pros:** Unified endpoint, gradual migration
**Cons:** Translation overhead (minimal)

---

## 🔀 OPTION 3: Dual Gateway Pattern

```mermaid
graph TB
    subgraph "Option 3: Dual Gateways"
        Client1[gRPC Clients]
        Client2[REST Clients]

        GatewayA[gRPC Gateway<br/>13395]
        GatewayB[REST Gateway<br/>13396]

        GraphOps3[GraphOps<br/>13398<br/>gRPC]
        Memory3[Memory Service<br/>13393<br/>REST]
        CoreAPI3[Core API<br/>13390<br/>REST]

        Client1 -->|gRPC| GatewayA
        Client2 -->|REST| GatewayB

        GatewayA -->|gRPC| GraphOps3
        GatewayB -->|REST| Memory3
        GatewayB -->|REST| CoreAPI3
    end

    style GatewayA fill:#9f9,stroke:#333,stroke-width:2px
    style GatewayB fill:#9f9,stroke:#333,stroke-width:2px
```

**Pros:** Protocol-specific optimizations
**Cons:** Two services to maintain

---

## 🌐 OPTION 4: Envoy Proxy

```mermaid
graph TB
    subgraph "Option 4: Envoy Universal Proxy"
        Clients[Any Client<br/>gRPC/REST/WebSocket]

        Envoy[Envoy Proxy<br/>13395<br/>Universal]

        subgraph "Envoy Features"
            Router[Advanced Router]
            Mesh[Service Mesh]
            Observe[Observability]
        end

        AllServices[All Services<br/>Any Protocol]

        Clients --> Envoy
        Envoy --> Router
        Envoy --> Mesh
        Envoy --> Observe
        Envoy --> AllServices
    end

    style Envoy fill:#9cf,stroke:#333,stroke-width:4px
```

**Pros:** Enterprise features, protocol agnostic
**Cons:** Complex configuration, overkill for current scale

---

## 📊 PROTOCOL FLOW: Hybrid Gateway (Recommended)

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant GraphOps
    participant Memory

    Note over Gateway: Hybrid Mode Active

    rect rgb(200, 255, 200)
        Note right of Client: gRPC → gRPC (native)
        Client->>Gateway: gRPC Request
        Gateway->>GraphOps: gRPC Forward
        GraphOps-->>Gateway: gRPC Response
        Gateway-->>Client: gRPC Response
    end

    rect rgb(255, 255, 200)
        Note right of Client: REST → REST (proxy)
        Client->>Gateway: HTTP/JSON Request
        Gateway->>Memory: HTTP Forward
        Memory-->>Gateway: HTTP/JSON Response
        Gateway-->>Client: HTTP/JSON Response
    end

    rect rgb(200, 220, 255)
        Note right of Client: REST → gRPC (translate)
        Client->>Gateway: HTTP/JSON Request
        Gateway->>Gateway: Translate to gRPC
        Gateway->>GraphOps: gRPC Request
        GraphOps-->>Gateway: gRPC Response
        Gateway->>Gateway: Translate to JSON
        Gateway-->>Client: HTTP/JSON Response
    end
```

---

## 🏗️ MIGRATION PATH

```mermaid
graph LR
    subgraph "Phase 1: Today"
        P1Gateway[Gateway<br/>gRPC-only]
        P1GraphOps[GraphOps<br/>gRPC ✅]
        P1Memory[Memory<br/>REST]
        P1Core[Core API<br/>REST]

        P1Gateway --> P1GraphOps
        P1Gateway -.x P1Memory
        P1Gateway -.x P1Core
    end

    subgraph "Phase 2: Hybrid"
        P2Gateway[Gateway<br/>Hybrid ✅]
        P2GraphOps[GraphOps<br/>gRPC ✅]
        P2Memory[Memory<br/>REST → gRPC]
        P2Core[Core API<br/>REST]

        P2Gateway --> P2GraphOps
        P2Gateway --> P2Memory
        P2Gateway --> P2Core
    end

    subgraph "Phase 3: Future"
        P3Gateway[Gateway<br/>gRPC-primary]
        P3GraphOps[GraphOps<br/>gRPC ✅]
        P3Memory[Memory<br/>gRPC ✅]
        P3Core[Core API<br/>REST]

        P3Gateway --> P3GraphOps
        P3Gateway --> P3Memory
        P3Gateway --> P3Core
    end

    P1Gateway ==> P2Gateway
    P2Gateway ==> P3Gateway

    style P1Gateway fill:#ff9,stroke:#333,stroke-width:2px
    style P2Gateway fill:#9f9,stroke:#333,stroke-width:3px
    style P3Gateway fill:#9cf,stroke:#333,stroke-width:2px
```

**Legend:**
- **Phase 1:** Current state (gRPC-only, incomplete)
- **Phase 2:** Hybrid gateway (REST proxy + gRPC native)
- **Phase 3:** Full gRPC with REST legacy support

---

## 🔧 ROUTING ARCHITECTURE

```mermaid
graph TD
    Client[Client Request]

    Gateway{Gateway<br/>Port 13395}

    subgraph "Routing Rules"
        PathMatch[Path Matching]
        ProtoDetect[Protocol Detection]
        LoadBalance[Load Balancing]
    end

    subgraph "Backends"
        Memory[Memory<br/>/api/v1/memory/*]
        GraphOps[GraphOps<br/>/api/v1/graph/*]
        CoreAPI[Core API<br/>/api/v1/core/*]
    end

    Client --> Gateway
    Gateway --> PathMatch
    PathMatch --> ProtoDetect
    ProtoDetect --> LoadBalance

    LoadBalance --> Memory
    LoadBalance --> GraphOps
    LoadBalance --> CoreAPI

    style Gateway fill:#9f9,stroke:#333,stroke-width:3px
    style PathMatch fill:#ff9,stroke:#333,stroke-width:2px
    style ProtoDetect fill:#f9f,stroke:#333,stroke-width:2px
```

---

## 🧪 TESTING FLOW

```mermaid
graph TD
    subgraph "Test Suite"
        T1[Test 1:<br/>REST → REST<br/>Proxy]
        T2[Test 2:<br/>gRPC → gRPC<br/>Native]
        T3[Test 3:<br/>REST → gRPC<br/>Translation]
        T4[Test 4:<br/>Failure<br/>Handling]
    end

    subgraph "Validation"
        V1[Response Code]
        V2[Response Time]
        V3[Data Integrity]
        V4[Error Messages]
    end

    T1 --> V1
    T1 --> V2
    T2 --> V1
    T2 --> V2
    T3 --> V1
    T3 --> V2
    T3 --> V3
    T4 --> V4

    style T3 fill:#f9f,stroke:#333,stroke-width:2px
    style V3 fill:#9f9,stroke:#333,stroke-width:2px
```

---

## 📈 PERFORMANCE EXPECTATIONS

```mermaid
graph LR
    subgraph "Latency Budget"
        Direct[Direct Access<br/>~5ms baseline]
        Proxy[REST Proxy<br/>+2ms overhead]
        Translate[Translation<br/>+5ms overhead]
    end

    subgraph "Targets"
        Target1[REST→REST: <10ms total]
        Target2[gRPC→gRPC: <8ms total]
        Target3[REST→gRPC: <15ms total]
    end

    Direct --> Target1
    Proxy --> Target1
    Direct --> Target2
    Translate --> Target3

    style Target1 fill:#9f9,stroke:#333,stroke-width:2px
    style Target2 fill:#9f9,stroke:#333,stroke-width:2px
    style Target3 fill:#ff9,stroke:#333,stroke-width:2px
```

---

**These diagrams support SPEC-132 decision-making process.**

**Generated:** October 22, 2025
**Format:** Mermaid (GitHub/GitLab compatible)
