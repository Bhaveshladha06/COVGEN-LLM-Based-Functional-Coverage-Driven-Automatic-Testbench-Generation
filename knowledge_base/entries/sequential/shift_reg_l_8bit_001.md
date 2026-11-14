---
id: "shift_reg_l_8bit_001"
context.module: "SHIFT_REG_L"
context.data_width: 8
context.type: "8-bit left shift register"
signals: ["clk", "rst_n", "sin", "dout"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the left shift register serially loading both bit values, the all-zero and all-one register states, and the serial output bit shifting out in both states.

## Notes
(none)

## RTL
```verilog
module shift_reg_l(clk, rst_n, sin, dout);
  input clk, rst_n, sin;
  output reg [7:0] dout;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) dout <= 8'b0;
    else        dout <= {dout[6:0], sin};
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_shift_l (ref logic [7:0] dout, ref logic sin) @(posedge clk);
  sin_cp : coverpoint sin {
    bins shift_zero = {0};
    bins shift_one  = {1};
  }
  dout_cp : coverpoint dout {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins mid      = {[8'h01:8'hFE]};
  }
  msb_cp : coverpoint dout[7] {
    bins low  = {0};
    bins high = {1};
  }
  sin_x_dout : cross sin_cp, dout_cp;
endgroup
```
