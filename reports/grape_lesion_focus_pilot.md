# Grape lesion-focus pilot

## Why the whole-leaf model preferred healthy

For the supplied `Guignardia_bidwellii_08.jpg`, the independently selected plant was
Grape, but the ResNet50 whole-leaf conditional distribution was healthy `61.58%`,
Black rot `30.73%`, Esca `6.75%`, and Leaf blight `0.95%`. Most pixels in the isolated
leaf view are green, while the pale field lesions differ from the controlled
PlantVillage appearance. The existing `65% + 15 pp` disease gate therefore withheld
the diagnosis. Because no class passed that gate, the old implementation also had no
target class for Grad-CAM.

## Experimental method

1. Keep independent plant identity and never use an ROI to change the plant.
2. Measure visible lesions inside the accepted leaf mask at original resolution.
3. Only when the full-leaf top condition is `healthy`, compare coverage with a
   host-specific healthy threshold.
4. For Grape, the threshold is the 99th percentile (`1.2959%`) from 323 accepted
   healthy PlantVillage training images, seed 42. Require at least two components and
   a largest component of at least `0.25%` of leaf area.
5. If the gate fires, neutralize all non-leaf pixels, take the two largest lesion ROIs,
   and average probabilities only within the already accepted Grape taxonomy.
6. Veto `healthy`, rerank the three disease candidates, and generate candidate
   Grad-CAM from the most supportive lesion ROI.

The ROI result remains evidence-only: it does not unlock diagnosis or management
guidance because its field calibration is unknown.

## Held-out audit

- Healthy Grape official test: 100 accepted images, `0/100` false healthy vetoes.
- All Grape official test: 755 accepted images; whole-leaf conditional accuracy
  `0.9947`, proposed accuracy `0.9947`, zero overrides, zero corrected, zero harmed.
- Other hosts were audited but are disabled because false-veto behavior and OpenCV
  acceptance were not consistently strong enough.

These controlled results show that the safeguard did not change the saturated
PlantVillage Grape result. They do **not** validate field accuracy.

## Supplied field image

- OpenCV: 25 regions, `12.42%` coverage, above the Grape healthy threshold.
- Whole leaf: healthy `61.58%`, Black rot `30.73%`.
- Two lesion ROIs after the healthy veto: Black rot relative score `97.86%`, Esca
  `1.38%`, Leaf blight `0.76%`.
- Final status: Black rot is the leading **candidate evidence**, diagnosis remains
  withheld, and a Black-rot-targeted focused Grad-CAM is generated.

The `97.86%` value is an uncalibrated within-ROI relative score, not a probability
that the plant has Black rot.

Machine-readable evidence is in
`reports/metrics/grape_lesion_focus_pilot.json`.
