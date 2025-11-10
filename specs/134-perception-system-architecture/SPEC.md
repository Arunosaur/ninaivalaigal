# SPEC-134: Perception System Architecture

**Status:** Draft
**Created:** 2025-10-28
**Updated:** 2025-10-28
**Owner:** AI Engineering Team
**Stakeholders:** Agent Development, Platform Architecture

---

## Executive Summary

Define a comprehensive perception system architecture for AI agents in Ninaivalaigal, supporting multiple perception modalities and enabling agents to understand and interact with diverse information sources. This SPEC establishes the foundation for advanced agent capabilities including visual understanding, structured data parsing, and tool-augmented perception.

---

## Problem Statement

Current AI agents in Ninaivalaigal are limited to text-only perception, which restricts their ability to:
- Understand visual content (screenshots, diagrams, UI elements)
- Parse structured data (HTML, DOM trees, accessibility trees)
- Interact with graphical user interfaces
- Leverage visual annotations for precise targeting
- Combine multiple perception modes for enhanced understanding

This limitation prevents agents from performing tasks that require visual reasoning, GUI automation, or multi-modal understanding.

---

## Goals

### Primary Goals
1. Define perception subtypes for different agent capabilities
2. Establish interfaces for perception system integration
3. Enable multi-modal reasoning and action
4. Support progressive capability enhancement

### Non-Goals
1. Implementing specific VLM (Vision-Language Model) backends (SPEC-136)
2. Building GUI automation frameworks (separate concern)
3. Training custom perception models

---

## Perception Subtypes

### 1. Text-Only Perception

**Description:** Traditional text-based input processing

**Capabilities:**
- Raw text content
- Markdown/formatted text
- Code snippets
- JSON/structured text

**Use Cases:**
- Code review and generation
- Document analysis
- API interactions
- Memory recall

**Implementation:**
```python
class TextPerception:
    def perceive(self, content: str) -> PerceptionResult:
        return PerceptionResult(
            type="text",
            content=content,
            metadata={"encoding": "utf-8", "length": len(content)}
        )
```

---

### 2. Multimodal Perception (VLM/MM-LLM)

**Description:** Vision-Language Models for image understanding

**Capabilities:**
- Image analysis and description
- Screenshot understanding
- Diagram interpretation
- Visual question answering
- Image-text reasoning

**Supported Models:**
- GPT-4V / GPT-4o
- Claude 3 (Opus, Sonnet, Haiku)
- Gemini Pro Vision
- LLaVA (open-source)

**Implementation:**
```python
class MultimodalPerception:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def perceive(
        self,
        image: bytes,
        prompt: str = "Describe this image"
    ) -> PerceptionResult:
        # Call VLM API
        response = self.call_vlm(image, prompt)
        return PerceptionResult(
            type="multimodal",
            content=response.text,
            visual_content=image,
            metadata={
                "model": self.model,
                "image_size": len(image),
                "tokens_used": response.tokens
            }
        )
```

**API Integration:**
```python
# Example usage
perception = MultimodalPerception(model="gpt-4o")
screenshot = capture_screenshot()
result = perception.perceive(
    image=screenshot,
    prompt="What buttons are visible on this screen?"
)
```

---

### 3. Structured Perception (HTML/DOM/A11y)

**Description:** Parse structured content representations

**Capabilities:**
- HTML parsing and extraction
- DOM tree traversal
- Accessibility tree analysis
- Semantic structure understanding
- Element relationships

**Data Structures:**
```python
@dataclass
class DOMNode:
    tag: str
    attributes: Dict[str, str]
    text_content: str
    children: List['DOMNode']
    xpath: str
    css_selector: str

@dataclass
class A11yNode:
    role: str  # button, link, textbox, etc.
    name: str  # Accessible name
    description: str
    value: Optional[str]
    states: List[str]  # focused, checked, expanded, etc.
    position: Tuple[int, int, int, int]  # x, y, width, height
```

**Implementation:**
```python
class StructuredPerception:
    def perceive_html(self, html: str) -> PerceptionResult:
        soup = BeautifulSoup(html, 'html.parser')
        dom_tree = self._build_dom_tree(soup)

        return PerceptionResult(
            type="structured_html",
            content=self._extract_text(soup),
            structured_data=dom_tree,
            metadata={"parser": "beautifulsoup4"}
        )

    def perceive_accessibility(self, a11y_tree: str) -> PerceptionResult:
        # Parse accessibility tree (e.g., from Chrome DevTools Protocol)
        nodes = self._parse_a11y_tree(a11y_tree)

        return PerceptionResult(
            type="structured_a11y",
            content=self._describe_a11y(nodes),
            structured_data=nodes,
            metadata={"source": "chrome_devtools"}
        )
```

**Use Cases:**
- Web scraping with semantic understanding
- GUI automation with accessibility APIs
- Form filling and validation
- Content extraction from structured documents

---

### 4. Set-of-Mark (SoM) and Visual Annotation

**Description:** Visual element marking for precise targeting

**Concept:**
- Overlay numerical or textual markers on visual elements
- Enable agents to reference specific UI components
- Support click, type, and interaction commands

**Annotation Types:**
1. **Bounding Box:** Draw rectangles around elements
2. **Numeric Labels:** Assign IDs to clickable elements
3. **Text Overlays:** Add descriptive labels
4. **Highlight Masks:** Color-code element types

**Implementation:**
```python
class SetOfMarkPerception:
    def annotate_screenshot(
        self,
        image: bytes,
        elements: List[UIElement]
    ) -> AnnotatedImage:
        """Add visual markers to screenshot"""
        img = Image.open(BytesIO(image))
        draw = ImageDraw.Draw(img)

        annotations = []
        for idx, elem in enumerate(elements):
            # Draw bounding box
            draw.rectangle(
                elem.bounds,
                outline="red",
                width=2
            )
            # Add numeric label
            draw.text(
                (elem.bounds[0], elem.bounds[1] - 20),
                f"[{idx}]",
                fill="red",
                font=self.font
            )
            annotations.append({
                "id": idx,
                "element": elem,
                "bounds": elem.bounds
            })

        return AnnotatedImage(
            image=img,
            annotations=annotations
        )

    def perceive_with_som(
        self,
        screenshot: bytes,
        ui_elements: List[UIElement]
    ) -> PerceptionResult:
        # Annotate screenshot
        annotated = self.annotate_screenshot(screenshot, ui_elements)

        # Send to VLM
        response = self.vlm.analyze(
            annotated.image,
            "Which element should I click to submit the form?"
        )

        # Parse response (e.g., "Click element [5]")
        element_id = self._extract_element_id(response)
        target_element = annotated.annotations[element_id]["element"]

        return PerceptionResult(
            type="som_annotation",
            content=response,
            action_target=target_element,
            metadata={"selected_element": element_id}
        )
```

**Protocols:**
- **SoM (Set-of-Mark):** Original protocol from Microsoft/UINav
- **GPT-4V with markers:** Overlay text/numbers on images
- **Grounding DINO:** Object detection with text prompts

---

### 5. Tool-Augmented Perception

**Description:** Enhance perception with external tools

**Tool Categories:**

**A. OCR (Optical Character Recognition)**
```python
class OCRPerception:
    def __init__(self, backend: str = "tesseract"):
        self.backend = backend

    def perceive(self, image: bytes) -> PerceptionResult:
        # Extract text from image
        text = pytesseract.image_to_string(Image.open(BytesIO(image)))

        # Get bounding boxes for words
        data = pytesseract.image_to_data(
            Image.open(BytesIO(image)),
            output_type=pytesseract.Output.DICT
        )

        return PerceptionResult(
            type="ocr",
            content=text,
            structured_data=self._build_word_boxes(data),
            metadata={"backend": self.backend}
        )
```

**B. Screenshot/Screen Capture**
```python
class ScreenCapturePerception:
    def capture_screen(self, region: Optional[Tuple] = None) -> bytes:
        screenshot = pyautogui.screenshot(region=region)
        buffer = BytesIO()
        screenshot.save(buffer, format="PNG")
        return buffer.getvalue()

    def capture_element(self, selector: str) -> bytes:
        # Use browser automation to capture element
        element = self.browser.find_element(selector)
        return element.screenshot_as_png
```

**C. Computer Vision**
```python
class CVPerception:
    def detect_objects(self, image: bytes) -> List[DetectedObject]:
        # Use YOLO, Faster R-CNN, or similar
        results = self.model.detect(image)
        return [
            DetectedObject(
                label=r.label,
                confidence=r.confidence,
                bbox=r.bbox
            )
            for r in results
        ]

    def find_template(
        self,
        screenshot: bytes,
        template: bytes,
        threshold: float = 0.8
    ) -> Optional[Tuple[int, int]]:
        # Template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        if len(locations[0]) > 0:
            return (locations[1][0], locations[0][0])
        return None
```

**Tool Orchestration:**
```python
class AugmentedPerception:
    def __init__(self):
        self.ocr = OCRPerception()
        self.cv = CVPerception()
        self.vlm = MultimodalPerception()

    def perceive_with_tools(
        self,
        image: bytes,
        tools: List[str] = ["ocr", "cv", "vlm"]
    ) -> PerceptionResult:
        results = {}

        if "ocr" in tools:
            results["ocr"] = self.ocr.perceive(image)

        if "cv" in tools:
            results["objects"] = self.cv.detect_objects(image)

        if "vlm" in tools:
            # Enhance VLM prompt with OCR/CV results
            context = self._build_context(results)
            results["vlm"] = self.vlm.perceive(
                image,
                f"Analyze this image. Context: {context}"
            )

        return PerceptionResult(
            type="augmented",
            content=self._synthesize_results(results),
            tool_outputs=results,
            metadata={"tools_used": tools}
        )
```

---

## Architecture

### Core Interfaces

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

@dataclass
class PerceptionResult:
    """Unified perception output"""
    type: str  # text, multimodal, structured, som, augmented
    content: str  # Main textual description
    visual_content: Optional[bytes] = None
    structured_data: Optional[Any] = None
    action_target: Optional[Any] = None
    tool_outputs: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

class Perceiver(ABC):
    """Base perception interface"""

    @abstractmethod
    def perceive(self, input: Any, **kwargs) -> PerceptionResult:
        """Process input and return perception result"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List supported perception types"""
        pass

class PerceptionPipeline:
    """Orchestrate multiple perception modules"""

    def __init__(self):
        self.perceivers: Dict[str, Perceiver] = {}

    def register(self, name: str, perceiver: Perceiver):
        self.perceivers[name] = perceiver

    def perceive(
        self,
        input: Any,
        modes: List[str] = ["text"]
    ) -> Dict[str, PerceptionResult]:
        results = {}
        for mode in modes:
            if mode in self.perceivers:
                results[mode] = self.perceivers[mode].perceive(input)
        return results
```

### System Integration

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Core                           │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Perception System                      │  │
│  │                                                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │   Text   │  │Multimodal│  │  Structured  │  │  │
│  │  │Perceiver │  │Perceiver │  │  Perceiver   │  │  │
│  │  └──────────┘  └──────────┘  └──────────────┘  │  │
│  │                                                   │  │
│  │  ┌──────────┐  ┌──────────────────────────────┐│  │
│  │  │   SoM    │  │  Tool-Augmented Perception   ││  │
│  │  │Perceiver │  │  (OCR, CV, Screen Capture)   ││  │
│  │  └──────────┘  └──────────────────────────────┘│  │
│  │                                                   │  │
│  │              ↓ Perception Results ↓              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Reasoning Engine                     │  │
│  │     (Process perception results → Actions)        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Execution System                       │  │
│  │       (Execute actions based on perception)       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)
- [ ] Implement core `Perceiver` interface
- [ ] Build `TextPerception` module
- [ ] Create `PerceptionResult` data structures
- [ ] Set up `PerceptionPipeline` orchestrator

### Phase 2: Multimodal (Weeks 3-4)
- [ ] Integrate VLM APIs (GPT-4V, Claude 3)
- [ ] Implement `MultimodalPerception`
- [ ] Add image preprocessing utilities
- [ ] Create vision prompt templates

### Phase 3: Structured Data (Weeks 5-6)
- [ ] Build HTML/DOM parser
- [ ] Implement accessibility tree parser
- [ ] Create `StructuredPerception` module
- [ ] Add element selector utilities

### Phase 4: Visual Annotation (Weeks 7-8)
- [ ] Implement Set-of-Mark annotation
- [ ] Build bounding box overlay system
- [ ] Create element targeting logic
- [ ] Integrate with GUI automation

### Phase 5: Tool Augmentation (Weeks 9-10)
- [ ] Integrate OCR (Tesseract, PaddleOCR)
- [ ] Add computer vision tools (YOLO, template matching)
- [ ] Implement screen capture utilities
- [ ] Build tool orchestration pipeline

---

## Testing Strategy

### Unit Tests
```python
def test_text_perception():
    perceiver = TextPerception()
    result = perceiver.perceive("Hello world")
    assert result.type == "text"
    assert result.content == "Hello world"

def test_multimodal_perception():
    perceiver = MultimodalPerception(model="gpt-4o")
    image = load_test_image("button.png")
    result = perceiver.perceive(image, "What is this?")
    assert "button" in result.content.lower()

def test_som_annotation():
    perceiver = SetOfMarkPerception()
    screenshot = load_test_image("form.png")
    elements = [
        UIElement(tag="button", bounds=(10, 10, 100, 50)),
        UIElement(tag="input", bounds=(10, 60, 200, 90))
    ]
    annotated = perceiver.annotate_screenshot(screenshot, elements)
    assert len(annotated.annotations) == 2
```

### Integration Tests
```python
def test_perception_pipeline():
    pipeline = PerceptionPipeline()
    pipeline.register("text", TextPerception())
    pipeline.register("vlm", MultimodalPerception())

    results = pipeline.perceive(
        test_image,
        modes=["text", "vlm"]
    )

    assert "text" in results
    assert "vlm" in results
```

---

## References

### Research Papers
1. **GPT-4V System Card** - OpenAI (2023)
2. **Set-of-Mark Prompting** - Microsoft Research (2023)
3. **Grounding DINO** - IDEA Research (2023)
4. **Visual Programming** - Google Research (2022)
5. **WebArena** - CMU/Microsoft (2023) - Web agent benchmarks

### Tools & Libraries
- **Vision APIs:** OpenAI GPT-4V, Anthropic Claude 3, Google Gemini
- **OCR:** Tesseract, PaddleOCR, EasyOCR
- **CV:** OpenCV, YOLO, Detectron2
- **DOM Parsing:** BeautifulSoup, lxml, Playwright
- **Accessibility:** Chrome DevTools Protocol, AXTree

### Related SPECs
- **SPEC-136:** Execution System Backends (GUI automation)
- **SPEC-135:** Multi-Agent Expert Protocol (perception expert)
- **SPEC-063:** Agentic Core Execution (perceiver subsystem)

---

## Success Metrics

1. **Perception Accuracy:** >90% correct element identification
2. **Multimodal Coverage:** Support for images, screenshots, diagrams
3. **Structured Parsing:** Parse 95% of web pages successfully
4. **Annotation Precision:** <5px targeting error for SoM
5. **Tool Integration:** 5+ augmentation tools operational

---

## Appendix

### Example: Full Perception Flow

```python
# Initialize perception system
pipeline = PerceptionPipeline()
pipeline.register("vlm", MultimodalPerception(model="gpt-4o"))
pipeline.register("som", SetOfMarkPerception())
pipeline.register("ocr", OCRPerception())

# Capture screenshot
screenshot = capture_screen()

# Get UI elements
ui_elements = get_ui_elements()  # From accessibility tree or DOM

# Multi-modal perception
results = pipeline.perceive(
    screenshot,
    modes=["vlm", "som", "ocr"]
)

# Agent reasoning
action = agent.reason(
    goal="Submit the form",
    perception=results
)

# Execute action
execute_action(action)  # SPEC-136
```

---

**End of SPEC-134**

---

## 📊 Implementation Status

**Last Updated:** January 2025
**Current Status:** 📋 **Not Implemented (0%)**

### ✅ Documentation (100%)

**SPEC Document:**
- ✅ Comprehensive specification document (`SPEC.md`)
- ✅ Defines 5 perception subtypes (Text, Multimodal, Structured, SoM, Tool-Augmented)
- ✅ Core interfaces (`Perceiver`, `PerceptionPipeline`, `PerceptionResult`)
- ✅ Implementation plan (5 phases, 10 weeks)
- ✅ Testing strategy
- ✅ Success metrics

### ❌ Missing (100%)

**Phase 1: Foundation (NOT STARTED)**
- ❌ Core `Perceiver` interface not implemented
- ❌ `TextPerception` module not created
- ❌ `PerceptionResult` data structures not implemented
- ❌ `PerceptionPipeline` orchestrator not created

**Phase 2: Multimodal (NOT STARTED)**
- ❌ VLM API integration (GPT-4V, Claude 3) not implemented
- ❌ `MultimodalPerception` module not created
- ❌ Image preprocessing utilities not created
- ❌ Vision prompt templates not created

**Phase 3: Structured Data (NOT STARTED)**
- ❌ HTML/DOM parser not implemented
- ❌ Accessibility tree parser not implemented
- ❌ `StructuredPerception` module not created
- ❌ Element selector utilities not created

**Phase 4: Visual Annotation (NOT STARTED)**
- ❌ Set-of-Mark annotation not implemented
- ❌ Bounding box overlay system not created
- ❌ Element targeting logic not implemented
- ❌ GUI automation integration not done

**Phase 5: Tool Augmentation (NOT STARTED)**
- ❌ OCR integration (Tesseract, PaddleOCR) not implemented
- ❌ Computer vision tools (YOLO, template matching) not integrated
- ❌ Screen capture utilities not implemented
- ❌ Tool orchestration pipeline not created

---

## 📋 Implementation Stories

**Story Verification (January 2025):**
- ✅ **US#602:** SPEC-134: Perception System Architecture (Done)
  - Confirmed: Related to SPEC-134
  - Status: Done (planning/design phase)
  - Tags: spec-134

**New Stories Created:**
- ✅ **US#864:** SPEC-134 Phase 1: Foundation (Core Interfaces & Text Perception) - HIGH Priority, 8 points, 2 weeks
- ✅ **US#865:** SPEC-134 Phase 2: Multimodal Perception (VLM Integration) - HIGH Priority, 13 points, 2 weeks
- ✅ **US#866:** SPEC-134 Phase 3: Structured Perception (HTML/DOM/A11y) - MEDIUM Priority, 10 points, 2 weeks
- ✅ **US#867:** SPEC-134 Phase 4: Visual Annotation (Set-of-Mark) - MEDIUM Priority, 10 points, 2 weeks
- ✅ **US#868:** SPEC-134 Phase 5: Tool-Augmented Perception (OCR, CV, Screen Capture) - MEDIUM Priority, 13 points, 2 weeks

**Total Estimated Effort:** 54 points, 10 weeks

---

## 🎯 Next Steps

1. ✅ **Analysis Complete** - Comprehensive analysis documents created
2. ✅ **Stories Created** - US#864-868 created
3. ⏳ **Begin Phase 1** - Start foundation implementation (US#864)
4. ⏳ **Update SPEC_INDEX.md** - Change status to "Not Implemented (0%)"
