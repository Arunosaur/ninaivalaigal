# TarangAI — Technical Slides
## Responsibilities
- Transport and delivery of memory bundles.
- Routing and buffering.
- Delivery guarantees.
## Components
- Stream router.
- Buffer manager.
- Audit hooks for FluxMind.
## Architecture
```mermaid
flowchart LR
  Tools --> Buf[Buffer] --> Router[TarangAI]
  Router --> NV[Ninaivalaigal+eM]
  Router --> SM[SmritiOS]
  Router --> PR[Pragna]
  Router --> FM[FluxMind]
```
