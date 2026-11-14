---
id: "mac_unit_001"
context.module: "MAC_UNIT"
context.data_width: 8
context.type: "multiply-accumulate unit"
signals: ["clk", "rst_n", "en", "clear", "a", "b", "acc", "ovf"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the multiply-accumulate unit accumulating products across operand ranges, the clear operation resetting the accumulator, holding when disabled, and the overflow flag asserting.

## Notes
(none)

## RTL
```verilog
module mac_unit(clk, rst_n, en, clear, a, b, acc, ovf);
  input clk, rst_n, en, clear;
  input [3:0] a, b;
  output reg [15:0] acc;
  output reg ovf;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc <= 16'b0; ovf <= 1'b0;
    end else if (clear) begin
      acc <= 16'b0; ovf <= 1'b0;
    end else if (en) begin
      {ovf, acc} <= acc + (a * b);
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mac (ref logic [3:0] a, b, ref logic [15:0] acc, ref logic en, clear, ovf) @(posedge clk);
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins accum = {1};
  }
  clear_cp : coverpoint clear {
    bins run   = {0};
    bins clear = {1};
  }
  ovf_cp : coverpoint ovf {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  a_x_b       : cross a_cp, b_cp;
  en_x_clear  : cross en_cp, clear_cp;
endgroup
```
