---
id: "shift_reg_bidir_8bit_001"
context.module: "SHIFT_REG_BIDIR"
context.data_width: 8
context.type: "8-bit bidirectional shift register"
signals: ["clk", "rst_n", "dir", "en", "sin", "dout"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the bidirectional shift register shifting in both directions, holding when disabled, and the cross of direction against enable to confirm every mode is exercised.

## Notes
(none)

## RTL
```verilog
module shift_reg_bidir(clk, rst_n, dir, en, sin, dout);
  input clk, rst_n, dir, en, sin;
  output reg [7:0] dout;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)   dout <= 8'b0;
    else if (en)  dout <= dir ? {sin, dout[7:1]} : {dout[6:0], sin};
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_shift_bidir (ref logic [7:0] dout, ref logic dir, en, sin) @(posedge clk);
  dir_cp : coverpoint dir {
    bins left  = {0};
    bins right = {1};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins shift = {1};
  }
  sin_cp : coverpoint sin {
    bins zero = {0};
    bins one  = {1};
  }
  dir_x_en  : cross dir_cp, en_cp;
  dir_x_sin : cross dir_cp, sin_cp;
endgroup
```
