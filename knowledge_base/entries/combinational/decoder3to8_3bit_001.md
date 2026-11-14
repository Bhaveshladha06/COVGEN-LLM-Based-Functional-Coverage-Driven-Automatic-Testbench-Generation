---
id: "decoder3to8_3bit_001"
context.module: "DECODER3TO8"
context.data_width: 3
context.type: "3-to-8 decoder"
signals: ["sel", "en", "y"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 3-to-8 decoder behavior for all select values with the enable asserted, the all-zero output when enable is deasserted, and the cross of select against enable.

## Notes
(none)

## RTL
```verilog
module decoder3to8(sel, en, y);
  input [2:0] sel;
  input en;
  output [7:0] y;
  assign y = en ? (8'b0000_0001 << sel) : 8'b0;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_dec38 (ref logic [2:0] sel, ref logic en, ref logic [7:0] y);
  sel_cp : coverpoint sel {
    bins s[] = {[0:7]};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  y_cp : coverpoint y {
    bins onehot[] = {8'h01, 8'h02, 8'h04, 8'h08, 8'h10, 8'h20, 8'h40, 8'h80};
    bins zero     = {8'h00};
  }
  sel_x_en : cross sel_cp, en_cp;
endgroup
```
