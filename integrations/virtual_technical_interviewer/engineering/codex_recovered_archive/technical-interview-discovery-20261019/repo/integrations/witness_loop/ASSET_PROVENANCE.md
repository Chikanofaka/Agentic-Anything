# WTL-029 v0.3 local artwork provenance

Engineering began 2026-10-16 and continued 2026-10-17 (Asia/Shanghai). These are local review assets. No supplied reference or generated derivative has been published, committed or pushed in this sprint. Public redistribution remains a human rights decision.

## Supplied references, inspected before implementation

The user supplied `WTL029_v0.3_Codex_Engineering_Handoff.zip` (SHA-256 `8dd19cdb0928b73677a167597552ae23afd00661dcb05967e55fe27dd99f664c`). Its four image hashes match `handoff_v03/REFERENCE_MANIFEST.json`. References were inspected visually and retained in the ignored local `handoff_v03/references/` directory. The reference package is not bundled in the app or source-delivery ZIP.

| Reference | Role and limitation |
|---|---|
| `linwu_anime_reference.png` | Silver hair, golden eyes, uniform and cap inspiration. Its cheerful salute was replaced with a tense, tired pose. |
| `rainy_platform_reference.png` | Rain, night lighting and station perspective inspiration. Its destination display and missing clues were not treated as canonical game evidence. |
| `evidence_prop_reference.png` | Paper/physical evidence mood reference. Its real transit tickets are not the Zhou Xu game ticket. |
| `clock_style_reference.png` | Analog clock mood reference; its time is incorrect for the game and it is not used as the evidence face. |

## Implemented local assets

| Path under `ui/assets/` | Creation and status |
|---|---|
| `platform_empty.png` | Built-in image-generation tool, reference-guided original station composition, 1672×941. Production candidate for this local playable; empty before the separate character layer appears. |
| `linwu_anxious.png` | Built-in image-generation tool, reference-guided adult dispatcher sprite, 1024×1536, PNG alpha preserved. Corner pixels were inspected as alpha 0. Anxiety, sleeve-clutching pose and cool night lighting replace the salute. |
| `clock_face.svg` | Original deterministic vector artwork, overlaid on the small scene clock to correct the generated clock hands. Hour angle 8.5° and minute angle 102° from twelve represent 00:17. |
| `clock_detail.svg` | Original deterministic vector close-up with correct hands and large exact `00:17`; expressly distinguishes a stopped reading from departure time. |
| `ticket_detail.svg` | Original vector fictional prop with exact `周序 / ZHOU XU`, fictional Yunjiang–Beichuan route, date 2026-10-16 and blank validation field. These printed prop details do not establish a journey, timestamp or hiding location. |
| `red_fabric_detail.svg` | Original vector inspection illustration of wet red fabric near lockers; no ownership claim. This is a stylized evidence illustration, not a photographic enlargement. |
| `train_departure_detail.svg` | Original vector inspection illustration of departing lights; no identifiable passengers or verified time. |

No final asset is fetched from a remote URL at runtime. The generated background's camera composition is identical in empty-platform and witness phases. Hotspot coordinates follow the actual image rather than the approximate reference script: clock (.739,.137), red fabric (.115,.45), ticket (.843,.71), train (.38,.47). The character occupies the middle foreground; the scene's evidence buttons remain independently reachable.

The SVG details are intentional precise game artwork, not substitutes falsely described as photographs. No generic CSS silhouette remains as the character. The generated images are art candidates; the actual-app screenshots in `engineering/wtl03-screenshots/` are separate runtime evidence.

## Generation prompts and method

Used the built-in image-generation facility through the [imagegen skill]([LOCAL_PATH_REDACTED]), not an API-key CLI. No user's OpenAI credential or gameplay API budget was used. Reference guidance and image generation do not establish publication rights.

Station prompt:

> Use case: stylized-concept. Asset: production game background, landscape 16:9, high resolution. Create a new polished cinematic anime visual novel background using the supplied rainy railway platform image ONLY as atmospheric inspiration. Completely empty fictional Yunjiang railway platform at midnight, no people, rain-soaked paving reflecting restrained warm station lamps and cold blue-grey rain. Beautiful hand-painted detailed mystery-game environment, realistic coherent perspective, moody yet objects clearly readable. Composition precise normalized coordinates: receding tracks and a very small departing train with two fading red tail lights at x=.20 y=.42; worn lockers on LEFT, near them red wet raincoat fabric at x=.18 y=.76; old round station clock hanging on a beam high at x=.78 y=.20 (small distant face, no other clock or timestamp); wooden bench in right foreground with a folded cream paper ticket at x=.70 y=.70. Leave central zone x=.38-.60 foreground spacious for a separately composited character. Lens wide and low but straight, canopy beams create depth. Keep all these props inside frame. Avoid suitcases and extraneous mystery props. No people or silhouettes, no lettering, no logos, no destination board or other numeric display, no UI, no captions, no watermark. The clue clock will have a precise 00:17 vector overlay in software, so subtle dark clock face acceptable. Beautiful atmospheric scene fills full image.

Character prompt:

> Use case: identity-preserve / stylized-concept. Asset: transparent PNG sprite for a cinematic detective visual novel, entire adult woman's figure from cap to upper thighs with all hair and both hands inside image, portrait 2:3. Use supplied character as appearance reference: pale silver long hair, gold eyes, railway staff cap, dark navy railway uniform with modest pale blue ribbon. Depict Lin Wu age27 adult night dispatcher with mature face and proportions. Change cheerful smile and saluting pose entirely: visibly tired, sleepless and anxious, brows subtly drawn upward with tension, eyes glancing toward an approaching investigator, mouth slightly parted as if startled, shoulders tight, hands gripping one sleeve near her waist, morally conflicted and guarded. No smile, no salute, no rosy cheerful cheeks, no childlike look. Elegant professional work-appropriate uniform, subtle rain droplets on shoulders, restrained cool-blue night rim lighting with small warm lamp highlights to match a dark rainy station. Detailed professional anime game illustration with painterly shading. Fully transparent background, isolated single character, no station, no scene, no caption, no text, no watermark; do not draw a checkerboard. Preserve crisp alpha edges and full cap/hair inside frame. Character's pose compact, arms not spread, ready for layering over existing background.

Requested and actual generated prop positions differ, so implementation uses visually inspected actual positions. The generated clock is corrected with an exact vector overlay; the evidence zoom is deterministic. Final app resource SHA-256 values are emitted by `scripts/build_witness_mac.sh` into `Contents/Resources/build-manifest.json`.
