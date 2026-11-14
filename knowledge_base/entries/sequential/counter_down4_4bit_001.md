---
id: "counter_down4_4bit_001"
context.module: "COUNTER_DOWN4"
context.data_width: 4
context.type: "4-bit down counter"
signals: ["clk", "rst_n", "en", "count", "zero"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the 4-bit down counter decrementing to zero, underflowing from zero back to the maximum value, the zero flag asserting, and holding while disabled.

## Notes
(none)

## RTL
```verilog
module counter_down4(clk, rst_n, en, count, zero);
  input clk, rst_n, en;
  output reg [3:0] count;
  output zero;
  assign zero = (count == 4'b0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'hF;
    else if (en) count <= count - 1'b1;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_cnt_dn4 (ref logic [3:0] count, ref logic en, zero) @(posedge clk);
  count_cp : coverpoint count {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  zero_cp : coverpoint zero {
    bins nonzero = {0};
    bins at_zero = {1};
  }
  count_trans_cp : coverpoint count {
    bins underflow = (0 => 15);
    bins to_zero   = (1 => 0);
    bins hold_zero = (0 => 0);
  }
  count_x_en : cross count_cp, en_cp;
endgroup
```
