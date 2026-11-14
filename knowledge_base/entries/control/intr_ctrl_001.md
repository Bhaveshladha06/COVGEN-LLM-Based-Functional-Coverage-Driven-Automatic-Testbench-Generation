---
id: "intr_ctrl_001"
context.module: "INTR_CTRL"
context.data_width: 4
context.type: "interrupt controller"
signals: ["clk", "rst_n", "irq_in", "mask", "irq_out", "pending"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the interrupt controller with each interrupt source asserted, masked and unmasked, multiple simultaneous interrupts, and the aggregated output asserting only when an unmasked source is pending.

## Notes
(none)

## RTL
```verilog
module intr_ctrl(clk, rst_n, irq_in, mask, irq_out, pending);
  input clk, rst_n;
  input [3:0] irq_in, mask;
  output irq_out;
  output reg [3:0] pending;
  assign irq_out = |(pending & ~mask);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) pending <= 4'b0;
    else        pending <= pending | irq_in;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_intr (ref logic [3:0] irq_in, mask, pending, ref logic irq_out) @(posedge clk);
  irq_cp : coverpoint irq_in {
    bins none     = {4'b0000};
    bins single[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    bins multiple = {[4'b0011:4'b0111], [4'b1001:4'b1111]};
  }
  mask_cp : coverpoint mask {
    bins none_masked = {4'b0000};
    bins all_masked  = {4'b1111};
    bins partial     = {[4'b0001:4'b1110]};
  }
  out_cp : coverpoint irq_out {
    bins quiet     = {0};
    bins asserting = {1};
  }
  irq_x_mask : cross irq_cp, mask_cp;
  mask_x_out : cross mask_cp, out_cp;
endgroup
```
