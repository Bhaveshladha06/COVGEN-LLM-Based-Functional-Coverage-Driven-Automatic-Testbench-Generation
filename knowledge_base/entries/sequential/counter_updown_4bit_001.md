---
id: "counter_updown_4bit_001"
context.module: "COUNTER_UPDOWN"
context.data_width: 4
context.type: "4-bit up/down counter"
signals: ["clk", "rst_n", "en", "up", "count"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the up/down counter counting in both directions, wrapping at the maximum when counting up and underflowing at zero when counting down, and the cross of direction against enable.

## Notes
(none)

## RTL
```verilog
module counter_updown(clk, rst_n, en, up, count);
  input clk, rst_n, en, up;
  output reg [3:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0;
    else if (en) count <= up ? (count + 1'b1) : (count - 1'b1);
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_cnt_ud (ref logic [3:0] count, ref logic en, up) @(posedge clk);
  count_cp : coverpoint count {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  up_cp : coverpoint up {
    bins counting_down = {0};
    bins counting_up   = {1};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  count_trans_cp : coverpoint count {
    bins wrap_up   = (15 => 0);
    bins wrap_down = (0 => 15);
  }
  up_x_en    : cross up_cp, en_cp;
  count_x_up : cross count_cp, up_cp;
endgroup
```
