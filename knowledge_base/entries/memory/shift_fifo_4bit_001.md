---
id: "shift_fifo_4bit_001"
context.module: "SHIFT_FIFO"
context.data_width: 4
context.type: "shift-register FIFO"
signals: ["clk", "rst_n", "push", "din", "dout", "valid"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the shift-register FIFO filling from empty to full, the valid flag asserting once data is present, and data propagating through every stage.

## Notes
(none)

## RTL
```verilog
module shift_fifo(clk, rst_n, push, din, dout, valid);
  input clk, rst_n, push;
  input [3:0] din;
  output [3:0] dout;
  output valid;
  reg [3:0] s0, s1, s2, s3;
  reg [2:0] fill;
  assign dout  = s3;
  assign valid = (fill != 3'd0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s0 <= 0; s1 <= 0; s2 <= 0; s3 <= 0; fill <= 0;
    end else if (push) begin
      s0 <= din; s1 <= s0; s2 <= s1; s3 <= s2;
      if (fill < 3'd4) fill <= fill + 1'b1;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_shift_fifo (ref logic [2:0] fill, ref logic [3:0] din, dout, ref logic push, valid) @(posedge clk);
  fill_cp : coverpoint fill {
    bins empty_f = {0};
    bins partial = {[1:3]};
    bins full_f  = {4};
    illegal_bins overflow = {[5:7]};
  }
  push_cp : coverpoint push {
    bins idle = {0};
    bins push = {1};
  }
  valid_cp : coverpoint valid {
    bins no_data  = {0};
    bins has_data = {1};
  }
  din_cp : coverpoint din {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  fill_x_push  : cross fill_cp, push_cp;
  valid_x_push : cross valid_cp, push_cp;
endgroup
```
