// Example points for the "Examples & guide" panel: {id, label, note}. Images come from img/<id>_2025_tc.webp.
// The pilot was labelled on the centre 10 m pixel, so no pilot label can be copied to the 210 m box as it is,
// and no pilot point was called crop by all five of us. These are the four pilot points where we split on
// crop vs not crop. Look at them together on the 210 m box (rule: crop if there is cropland anywhere in it),
// agree, then replace "to discuss" with the agreed label and say in the note what decided it.
window.EXAMPLES = [
  {id: "P01", label: "to discuss", note: "Pilot, centre pixel: 2 crop, 3 not crop. One note: \"clear field shapes from Google Maps\"."},
  {id: "P12", label: "to discuss", note: "Pilot, centre pixel: 3 crop, 2 not crop; lowest confidence 1."},
  {id: "P20", label: "to discuss", note: "Pilot, centre pixel: 2 crop, 2 not crop, 1 unsure."},
  {id: "P24", label: "to discuss", note: "Pilot, centre pixel: 2 crop, 2 not crop, 1 unsure."}
];
