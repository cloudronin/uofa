A.1 Mesh Statistics

Global meshes:
- Coarse (10 mm): 182,340 elements (C3D8R 126,112; S4R 56,228); min Jacobian 0.48; avg skewness 0.22.
- Baseline (7 mm): 398,772 elements (C3D8R 271,336; S4R 127,436); min Jacobian 0.45; avg skewness 0.24.
- Fine (5 mm): 771,905 elements (C3D8R 515,900; S4R 256,005); min Jacobian 0.43; avg skewness 0.26.
- Hourglass energy fraction: 3.1–3.6% peak across cases.

Submodel:
- 1,246,118 C3D8R/C3D4H elements locally; min Jacobian 0.41; target edge 1.0 mm at toe, 0.5 mm at root fillet.

A.2 Test Setup and Instrumentation

Corner drop:
- Orientation: Roll 0°, Pitch 15°, Yaw 45°; verified with dual-axis digital inclinometers (±0.1°).
- Accelerometers: PCB 356A45, SNs 10483, 10484, 10485; mounting via wax per spec; calibration dates 2026-06-10.
- DIC: Two 12-bit cameras, 1280x800 at 10 kHz, lens 50 mm f/2.8; speckle size 3 px; stereo calibration residual 0.12 px.
- Strain gauge: Vishay 3-element rosette, 350 Ω, gauge factor 2.08, adhesive M-Bond 200; cured 2 hours at 60 C.

Crush:
- Load cell: Interface 1200 series, 50 kN, SN 7832; calibration 2026-05-27; combined error 0.03%.
- LVDT: Macro Sensors GHS series, ±25 mm, SN 33421.

A.3 Material Characterization

6061-T6:
- Quasi-static (3 coupons): Yield 271–276 MPa, UTS 314–320 MPa, elongation 12–14%.
- SHPB (3 coupons): True stress at 10% strain was 320–335 MPa at ~100 1/s. Fitting yielded C = 0.013–0.017.
- Plots: Provided as PDFs, filenames mat_AL6061_rateQS.pdf, mat_AL6061_rateSHPB.pdf.

Weld metal (ER4043):
- Microhardness HV0.5 across fusion line: 68–77 HV; base 6061-T6 in HAZ: 72–84 HV. Adopted weld σy scale 0.92 baseline (range 0.85–1.00).

A.4 Equipment and Calibration Certificates

- PCB accelerometer certs: pcb356A45_cert_10483.pdf, …_10485.pdf.
- Interface load cell cert: interface1200_cert_7832.pdf.
- DIC camera calibration: dic_stereo_cal_2026-06-11.pdf.
- Ultrasonic bolt elongation device: Sonelastic cert se-2026-05-15.pdf.

A.5 Sensitivity Study Matrices

One-at-a-time sweeps:
- μ = 0.20, 0.25, 0.30
- Weld scale = 0.85, 0.92, 1.00
- Cover thickness = 1.9, 2.0, 2.1 mm
- Preload = 13.5, 15.0, 16.5 kN

Latin hypercube (60 runs):
- Inputs: μ, weld scale, cover thickness
- Output ranges observed:
  - Intrusion: 2.61–2.94 mm
  - Peak g (center): 34.6–37.2 g
  - Toe strain (crush): 3.4–4.5%

A.6 Reproduction Instructions

- Clone repo: git clone git@gitlab.company/mech-bp/BME-DROP.git
- Checkout tag: git checkout R02
- Set environment: singularity run abaqus2024hf2.sif
- Baseline drop: python run_all.py —case drop —mesh 7mm
- Baseline crush: python run_all.py —case crush —mesh 7mm
- Submodel: python run_submodel.py —source odbs/drop_baseline.odb —region weld_toe_NE
- Post-process: python extract_qois.py —odb odbs/drop_baseline.odb

Expected outputs:
- Intrusion: 2.78±0.02 mm
- Peak g: 35.4±0.2 g
- Toe strain (avg, crush): 3.8±0.1%
