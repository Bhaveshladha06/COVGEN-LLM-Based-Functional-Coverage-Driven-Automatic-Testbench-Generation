---
id: "johnson_counter_4bit_001"
context.module: "JOHNSON_COUNTER"
context.data_width: 4
context.type: "4-bit Johnson counter"
signals: ["clk", "rst_n", "en", "count"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the Johnson counter visiting all eight valid states in its sequence, completing a full cycle, and holding while the enable is deasserted.

## Notes
(none)

## RTL
```verilog
module johnson_counter(clk, rst_n, en, count);
  input clk, rst_n, en;
  output reg [3:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0000;
    else if (en) count <= {~count[0], count[3:1]};
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_johnson (ref logic [3:0] count, ref logic en) @(posedge clk);
  count_cp : coverpoint count {
    bins valid[] = {4'b0000, 4'b1000, 4'b1100, 4'b1110,
                    4'b1111, 4'b0111, 4'b0011, 4'b0001};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins shift = {1};
  }
  count_trans_cp : coverpoint count {
    bins fill_start  = (4'b0000 => 4'b1000);
    bins fill_done   = (4'b1110 => 4'b1111);
    bins empty_start = (4'b1111 => 4'b0111);
    bins empty_done  = (4'b0001 => 4'b0000);
  }
  count_x_en : cross count_cp, en_cp;
endgroup
```
