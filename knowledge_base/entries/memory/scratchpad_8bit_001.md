---
id: "scratchpad_8bit_001"
context.module: "SCRATCHPAD"
context.data_width: 8
context.type: "byte-enabled scratchpad memory"
signals: ["clk", "we", "be", "addr", "din", "dout"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the byte-enabled scratchpad writing with each byte-enable pattern including none and all bytes enabled, across the address range, crossing byte enable against write enable.

## Notes
(none)

## RTL
```verilog
module scratchpad(clk, we, be, addr, din, dout);
  input clk, we;
  input [1:0] be;
  input [2:0] addr;
  input [15:0] din;
  output reg [15:0] dout;
  reg [15:0] mem [0:7];
  always @(posedge clk) begin
    if (we) begin
      if (be[0]) mem[addr][7:0]  <= din[7:0];
      if (be[1]) mem[addr][15:8] <= din[15:8];
    end
    dout <= mem[addr];
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_scratchpad (ref logic [1:0] be, ref logic [2:0] addr, ref logic we) @(posedge clk);
  be_cp : coverpoint be {
    bins none      = {2'b00};
    bins lower     = {2'b01};
    bins upper     = {2'b10};
    bins both      = {2'b11};
  }
  addr_cp : coverpoint addr {
    bins first  = {0};
    bins mid    = {[1:6]};
    bins last   = {7};
  }
  we_cp : coverpoint we {
    bins read  = {0};
    bins write = {1};
  }
  be_x_we   : cross be_cp, we_cp;
  addr_x_we : cross addr_cp, we_cp;
endgroup
```
