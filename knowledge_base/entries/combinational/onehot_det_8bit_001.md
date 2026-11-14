---
id: "onehot_det_8bit_001"
context.module: "ONEHOT_DET"
context.data_width: 8
context.type: "one-hot detector"
signals: ["din", "is_onehot"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the one-hot detector for genuine one-hot inputs, the all-zero input, and multi-bit inputs, crossing the input class against the detector output.

## Notes
(none)

## RTL
```verilog
module onehot_det(din, is_onehot);
  input [7:0] din;
  output is_onehot;
  assign is_onehot = (din != 8'b0) && ((din & (din - 1)) == 8'b0);
endmodule
```

## Coverage model
```systemverilog
covergroup cg_onehot (ref logic [7:0] din, ref logic is_onehot);
  din_cp : coverpoint din {
    bins onehot[]  = {8'h01, 8'h02, 8'h04, 8'h08, 8'h10, 8'h20, 8'h40, 8'h80};
    bins zero      = {8'h00};
    bins multi     = {[8'h03:8'h07], [8'h09:8'h0F]};
  }
  det_cp : coverpoint is_onehot {
    bins not_onehot = {0};
    bins onehot     = {1};
  }
  din_x_det : cross din_cp, det_cp;
endgroup
```
