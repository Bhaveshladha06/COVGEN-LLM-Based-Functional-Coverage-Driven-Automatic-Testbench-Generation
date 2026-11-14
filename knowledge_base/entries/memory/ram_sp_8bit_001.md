---
id: "ram_sp_8bit_001"
context.module: "RAM_SP"
context.data_width: 8
context.type: "single-port RAM"
signals: ["clk", "we", "addr", "din", "dout"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the single-port RAM writing and reading across the low, middle, and high address ranges, the boundary addresses, and the cross of write enable against address range.

## Notes
(none)

## RTL
```verilog
module ram_sp(clk, we, addr, din, dout);
  input clk, we;
  input [3:0] addr;
  input [7:0] din;
  output reg [7:0] dout;
  reg [7:0] mem [0:15];
  always @(posedge clk) begin
    if (we) mem[addr] <= din;
    dout <= mem[addr];
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_ram_sp (ref logic [3:0] addr, ref logic [7:0] din, dout, ref logic we) @(posedge clk);
  addr_cp : coverpoint addr {
    bins first = {0};
    bins low   = {[1:7]};
    bins high  = {[8:14]};
    bins last  = {15};
  }
  we_cp : coverpoint we {
    bins read  = {0};
    bins write = {1};
  }
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  addr_x_we : cross addr_cp, we_cp;
endgroup
```
