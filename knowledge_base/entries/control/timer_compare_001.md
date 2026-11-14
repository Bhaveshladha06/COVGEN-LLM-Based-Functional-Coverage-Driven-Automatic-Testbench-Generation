---
id: "timer_compare_001"
context.module: "TIMER_COMPARE"
context.data_width: 8
context.type: "timer with compare match"
signals: ["clk", "rst_n", "en", "compare", "counter", "match"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the compare timer counting to the compare value, asserting the match output, restarting from zero after a match, compare values at the extremes, and holding while disabled.

## Notes
(none)

## RTL
```verilog
module timer_compare(clk, rst_n, en, compare, counter, match);
  input clk, rst_n, en;
  input [7:0] compare;
  output reg [7:0] counter;
  output match;
  assign match = (counter == compare);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)      counter <= 8'b0;
    else if (en)     counter <= match ? 8'b0 : (counter + 1'b1);
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_timer_cmp (ref logic [7:0] compare, counter, ref logic en, match) @(posedge clk);
  compare_cp : coverpoint compare {
    bins immediate = {8'h00};
    bins short     = {[8'h01:8'h7F]};
    bins long      = {[8'h80:8'hFE]};
    bins max       = {8'hFF};
  }
  counter_cp : coverpoint counter {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  match_cp : coverpoint match {
    bins no_match = {0};
    bins matched  = {1};
  }
  en_cp : coverpoint en {
    bins stopped = {0};
    bins running = {1};
  }
  compare_x_match : cross compare_cp, match_cp;
  en_x_counter    : cross en_cp, counter_cp;
endgroup
```
