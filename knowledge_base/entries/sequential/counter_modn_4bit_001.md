---
id: "counter_modn_4bit_001"
context.module: "COUNTER_MODN"
context.data_width: 4
context.type: "modulo-N counter"
signals: ["clk", "rst_n", "en", "count", "tc"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the modulo-N counter reaching its terminal count, rolling over to zero, asserting the terminal count flag, and holding while the enable is deasserted.

## Notes
(none)

## RTL
```verilog
module counter_modn(clk, rst_n, en, count, tc);
  input clk, rst_n, en;
  output reg [3:0] count;
  output tc;
  parameter N = 10;
  assign tc = (count == N - 1);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0;
    else if (en) count <= tc ? 4'b0 : (count + 1'b1);
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_cnt_modn (ref logic [3:0] count, ref logic en, tc) @(posedge clk);
  count_cp : coverpoint count {
    bins zero     = {0};
    bins mid      = {[1:8]};
    bins terminal = {9};
    illegal_bins out_of_range = {[10:15]};
  }
  tc_cp : coverpoint tc {
    bins not_terminal = {0};
    bins terminal     = {1};
  }
  count_trans_cp : coverpoint count {
    bins rollover = (9 => 0);
    bins step     = (0 => 1);
  }
  count_x_tc : cross count_cp, tc_cp;
endgroup
```
