---
id: "jkff_1bit_001"
context.module: "JKFF"
context.data_width: 1
context.type: "JK flip-flop"
signals: ["clk", "rst_n", "j", "k", "q"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the JK flip-flop across all four input combinations covering hold, reset, set, and toggle behaviour, and both output transition directions.

## Notes
(none)

## RTL
```verilog
module jkff(clk, rst_n, j, k, q);
  input clk, rst_n, j, k;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else begin
      case ({j, k})
        2'b00: q <= q;
        2'b01: q <= 1'b0;
        2'b10: q <= 1'b1;
        2'b11: q <= ~q;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_jkff (ref logic j, k, q) @(posedge clk);
  jk_cp : coverpoint {j, k} {
    bins hold   = {2'b00};
    bins clear  = {2'b01};
    bins set    = {2'b10};
    bins toggle = {2'b11};
  }
  q_cp : coverpoint q {
    bins low  = {0};
    bins high = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
  }
  jk_x_q : cross jk_cp, q_cp;
endgroup
```
