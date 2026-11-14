---
id: "ram_dp_8bit_001"
context.module: "RAM_DP"
context.data_width: 8
context.type: "dual-port RAM"
signals: ["clk", "we_a", "addr_a", "din_a", "dout_a", "addr_b", "dout_b"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the dual-port RAM writing on port A while reading on port B, both ports addressing the same location simultaneously, and address coverage across the full range on both ports.

## Notes
(none)

## RTL
```verilog
module ram_dp(clk, we_a, addr_a, din_a, dout_a, addr_b, dout_b);
  input clk, we_a;
  input [3:0] addr_a, addr_b;
  input [7:0] din_a;
  output reg [7:0] dout_a, dout_b;
  reg [7:0] mem [0:15];
  always @(posedge clk) begin
    if (we_a) mem[addr_a] <= din_a;
    dout_a <= mem[addr_a];
    dout_b <= mem[addr_b];
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_ram_dp (ref logic [3:0] addr_a, addr_b, ref logic we_a) @(posedge clk);
  addr_a_cp : coverpoint addr_a {
    bins low  = {[0:7]};
    bins high = {[8:15]};
  }
  addr_b_cp : coverpoint addr_b {
    bins low  = {[0:7]};
    bins high = {[8:15]};
  }
  we_cp : coverpoint we_a {
    bins idle  = {0};
    bins write = {1};
  }
  addr_a_x_b  : cross addr_a_cp, addr_b_cp;
  we_x_addr_a : cross we_cp, addr_a_cp;
endgroup
```
