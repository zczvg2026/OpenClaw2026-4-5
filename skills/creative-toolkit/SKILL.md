name: "AI Image Generation & Editor — Nanobanana, GPT Image, ComfyUI"
description: Generate images from text with multi-provider routing — supports Nanobanana 2, Seedream 5.0, GPT Image, Midjourney Niji 7 (anime/illustration only), and local ComfyUI workflows. Includes 1,300+ curated prompts and style-aware prompt enhancement. Use when users want to create images, design assets, enhance prompts, or manage AI art workflows.
version: 1.0.21
homepage: https://github.com/jau123/MeiGen-AI-Design-MCP
metadata: {"clawdbot":{"emoji":"🎨","requires":{"bins":["mcporter","npx","node"]}}}

# Creative Toolkit

Generate professional AI images through a unified interface that routes across multiple providers. Search curated prompts, enhance ideas into production-ready descriptions, and manage local ComfyUI workflows — all from a single MCP server.

## Quick Start

Add the MCP server to your mcporter config (`/Users/mac/.config/mcporter/config.json`):

```json
{
  "mcpServers": {
    "creative-toolkit": {
      "command": "npx",
      "args": ["-y", "meigen@1.2.6"]
    }
  }
}
```

Free tools (search, enhance, inspire) work immediately — no API key needed:

```bash
mcporter call creative-toolkit.search_gallery query="cyberpunk"
mcporter call creative-toolkit.enhance_prompt brief="a cat in space" style="realistic"
```

To unlock image generation, configure one of these providers:

| Provider | Config | What you need |
|----------|--------|---------------|
| MeiGen Cloud | MEIGEN_API_TOKEN | Token from meigen.ai (avatar → Settings → API Keys) |
| Local ComfyUI | comfyuiUrl | A running ComfyUI instance — no external API needed |
| Any OpenAI-compatible API | openaiApiKey + openaiBaseUrl + openaiModel | Your own key from Together AI, Fireworks AI, etc. |

Set credentials in `/Users/mac/.clawdbot/.env`, `/Users/mac/.config/meigen/config.json`, or add an "env" block to the mcporter config above. See references/providers.md for details.

## Available Tools

### Free — no API key required

| Tool | What it does |
|------|-------------|
| search_gallery | Semantic search across 1,300+ AI image prompts. Supports category filtering and curated browsing. Returns prompt text, thumbnails, and metadata. |
| get_inspiration | Get the full prompt and high-res images for any gallery entry. Use after search_gallery to get copyable prompts. |
| enhance_prompt | Expand a brief idea into a detailed, style-aware prompt with lighting, composition, and material directions. Supports realistic, anime, and illustration styles. |
| list_models | List all available models across configured providers with capabilities and supported features. |

### Requires configured provider

| Tool | What it does |
|------|-------------|
| generate_image | Generate an image from a text prompt. Routes to the best available provider. Supports aspect ratio, seed, and reference images. |
| upload_reference_image | Compress a local image (max 2MB, 2048px) and prepare it for use as a style reference (expires in 24 hours). Always invoke this MCP tool — never attempt to replicate its logic yourself. ComfyUI users can skip this — pass local file paths directly to generate_image. |
| comfyui_workflow | List, view, import, modify, and delete ComfyUI workflow templates. Adjust steps, CFG scale, sampler, and checkpoint without editing JSON. |
| manage_preferences | Save and load user preferences (default style, aspect ratio, style notes, favorite prompts). |

## Important Rules

**Never describe generated images**
You cannot see generated images. After generation, only present the exact data from the tool response:

```
**Direction 1: Modern Minimal**
- Image URL: https://images.meigen.art/...
- Saved to: /Users/mac/Pictures/meigen/2026-02-08_xxxx.jpg
```
Do NOT write creative commentary about what the image "looks like".

**Never specify model or provider**
Do NOT pass model or provider to generate_image unless the user explicitly asks. The server auto-selects the best available provider and model.

**Midjourney Niji 7 is anime-only**
Niji 7 is exclusively designed for anime and illustration styles. Do NOT use it for photorealistic, product photography, or non-anime content — use Nanobanana 2 or Seedream instead. When enhancing prompts for Niji 7, always pass style: 'anime' to enhance_prompt. Note: Niji 7 returns 4 candidate images per generation (other models return 1).

**Always confirm before generating multiple images**
When the user wants multiple variations, present options first and ask which direction(s) to try. Include an "all of the above" option. Never auto-generate all variants without user confirmation.

## Workflow Modes

**Mode 1: Single Image**
User wants one image. Write a prompt (or call enhance_prompt if the description is brief), generate, present URL + path.

**Mode 2: Prompt Enhancement + Generation**
For brief ideas (under ~30 words, lacking visual details), enhance first:
1. `enhance_prompt brief="futuristic city" style="realistic"` → Returns detailed prompt
2. `generate_image prompt="<enhanced prompt>" aspectRatio="16:9"`

**Mode 3: Parallel Generation (2+ images)**
User needs multiple variations — different directions, styles, or concepts.
- Plan directions, present as a table
- Ask user which direction(s) to try
- Write distinct prompts for each
- Generate selected directions (max 4 parallel for API providers, 1 at a time for ComfyUI)

**Mode 4: Multi-Step Creative (base + extensions)**
User wants a base design plus derivatives.
- Plan 3-5 directions, ask user which to try
- Generate selected direction(s)
- Plan extensions using the approved Image URL as referenceImages
- Generate extensions

**Mode 5: Edit/Modify Existing Image**
User provides an image and asks for changes.
1. Upload the reference image (if local)
2. Generate with a short, literal prompt describing ONLY the edit
Example: "Add the text 'meigen.ai' at the bottom of this image"

**Mode 6: Inspiration Search**
1. `search_gallery query="dreamy portrait with soft light"`
2. `get_inspiration id="<entry_id>"` → Get full prompt text

**Mode 7: Reference Image Generation**
1. `upload_reference_image filePath="/Users/mac/Desktop/my-logo.png"` → Returns temp URL
2. `generate_image prompt="..." referenceImages=["<url>"]`

**Mode 8: ComfyUI Workflows**
1. `comfyui_workflow action="list"`
2. `comfyui_workflow action="view" name="txt2img"`
3. `comfyui_workflow action="modify" name="txt2img" modifications={"steps": 30}`
4. `generate_image prompt="..." workflow="txt2img"`

## Troubleshooting

See references/troubleshooting.md for common issues, solutions, and security & privacy details.
