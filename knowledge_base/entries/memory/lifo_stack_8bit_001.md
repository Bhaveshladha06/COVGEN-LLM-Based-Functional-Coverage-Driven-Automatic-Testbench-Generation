---
id: "lifo_stack_8bit_001"
context.module: "LIFO_STACK"
context.data_width: 8
context.type: "LIFO stack"
signals: ["clk", "rst_n", "push", "pop", "din", "dout", "full", "empty"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the stack pushing until full, popping until empty, push attempts while full and pop attempts while empty being ignored, and the cross of push against pop.

## Notes
(none)

## RTL
```verilog
module lifo_stack(clk, rst_n, push, pop, din, dout, full, empty);
  input clk, rst_n, push, pop;
  input [7:0] din;
  output [7:0] dout;
  output full, empty;
  reg [7:0] mem [0:7];
  reg [3:0] sp;
  assign full  = (sp == 4'd8);
  assign empty = (sp == 4'd0);
  assign dout  = empty ? 8'b0 : mem[sp - 1'b1];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) sp <= 0;
    else if (push && !full) begin mem[sp] <= din; sp <= sp + 1'b1; end
    else if (pop && !empty) sp <= sp - 1'b1;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_stack (ref logic [3:0] sp, ref logic push, pop, full, empty) @(posedge clk);
  sp_cp : coverpoint sp {
    bins empty_s = {0};
    bins mid     = {[1:7]};
    bins full_s  = {8};
    illegal_bins overflow = {[9:15]};
  }
  push_cp : coverpoint push {
    bins idle = {0};
    bins push = {1};
  }
  pop_cp : coverpoint pop {
    bins idle = {0};
    bins pop  = {1};
  }
  full_cp : coverpoint full {
    bins not_full = {0};
    bins is_full  = {1};
  }
  empty_cp : coverpoint empty {
    bins not_empty = {0};
    bins is_empty  = {1};
  }
  push_x_pop   : cross push_cp, pop_cp;
  push_x_full  : cross push_cp, full_cp;
  pop_x_empty  : cross pop_cp, empty_cp;
endgroup
```
