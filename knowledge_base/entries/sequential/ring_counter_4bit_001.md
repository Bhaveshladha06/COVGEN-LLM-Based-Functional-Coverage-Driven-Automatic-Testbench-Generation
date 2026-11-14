---
id: "ring_counter_4bit_001"
context.module: "RING_COUNTER"
context.data_width: 4
context.type: "4-bit ring counter"
signals: ["clk", "rst_n", "en", "count"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the ring counter visiting every one-hot state, completing a full rotation back to the initial state, and treating any non-one-hot state as illegal.

## Notes
(none)

## RTL
```verilog
module ring_counter(clk, rst_n, en, count);
  input clk, rst_n, en;
  output reg [3:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0001;
    else if (en) count <= {count[2:0], count[3]};
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_ring (ref logic [3:0] count, ref logic en) @(posedge clk);
  count_cp : coverpoint count {
    bins s0 = {4'b0001};
    bins s1 = {4'b0010};
    bins s2 = {4'b0100};
    bins s3 = {4'b1000};
    illegal_bins not_onehot = default;
  }
  en_cp : coverpoint en {
    bins hold   = {0};
    bins rotate = {1};
  }
  count_trans_cp : coverpoint count {
    bins rot0 = (4'b0001 => 4'b0010);
    bins rot1 = (4'b0010 => 4'b0100);
    bins rot2 = (4'b0100 => 4'b1000);
    bins rot3 = (4'b1000 => 4'b0001);
  }
  count_x_en : cross count_cp, en_cp;
endgroup
```
