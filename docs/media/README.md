# Classroom media

Presentation preference, 2026-09-23: **light mode only**, white backgrounds, readable dark text, green accents, and activity-focused copy. Use “Local AI on Jetson Nano” and descriptive experiment names. Keep technical limitations and validation boundaries in presenter notes and documentation, not audience-facing slides or routine menu banners. Runtime errors and required user actions must remain visible and accurate.

The current PPT contains only implemented menu entries. Do not claim physical-board validation, performance or model accuracy without actual evidence. Preserve earlier standalone code and the archived catalogue separately from the active programme.

- `render_presentation.mjs`: editable PPTX authoring source using the bundled Artifact Tool presentation runtime. Set `PRESENTATION_SKILL_DIR`, `RUNTIME_NODE_MODULES`, and `RUNTIME_PYTHON`, make the bundled Node modules resolvable, then pass a fresh output workspace directory. The script validates the output before delivery. Render and inspect every final slide.
- `render_walkthrough.swift`: macOS terminal-text video authoring with AppKit/AVFoundation. Pass a fresh output directory. This generates instructional commands; it never captures desktop windows or pretends to execute Nano commands.
- `jetson-nano-setup.mp4`: current light-mode command walkthrough.
- `nano-product.jpeg`: NVIDIA product photograph, embedded on the cover without alteration. Source attribution is also in slide notes.

Image source: [NVIDIA Jetson Nano product development](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-nano/product-development/).

Original image URL: https://www.nvidia.com/content/nvidiaGDC/us/en_US/autonomous-machines/embedded-systems/jetson-nano/product-development/_jcr_content/root/responsivegrid/nv_container_1169488117/nv_container_copy/nv_image.coreimg.jpeg/1710770678070/jetson-nano-2560x1440.jpeg
