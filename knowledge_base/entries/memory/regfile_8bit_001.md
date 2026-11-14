---
id: "regfile_8bit_001"
context.module: "REGFILE"
context.data_width: 8
context.type: "register file"
signals: ["clk", "rst_n", "we", "waddr", "wdata", "raddr1", "rdata1", "raddr2", "rdata2"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the register file writing to every register, reading from both read ports across the full address range, the read-during-write hazard where a read address matches the write address, and register zero being addressed.

## Notes
(none)

## RTL
```verilog
module regfile(clk, rst_n, we, waddr, wdata, raddr1, rdata1, raddr2, rdata2);
  input clk, rst_n, we;
  input [2:0] waddr, raddr1, raddr2;
  input [7:0] wdata;
  output [7:0] rdata1, rdata2;
  reg [7:0] regs [0:7];
  integer i;
  assign rdata1 = regs[raddr1];
  assign rdata2 = regs[raddr2];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) for (i = 0; i < 8; i = i + 1) regs[i] <= 8'b0;
    else if (we) regs[waddr] <= wdata;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_regfile (ref logic [2:0] waddr, raddr1, raddr2, ref logic we) @(posedge clk);
  waddr_cp : coverpoint waddr {
    bins reg_zero = {0};
    bins others[] = {[1:7]};
  }
  raddr1_cp : coverpoint raddr1 {
    bins reg_zero = {0};
    bins others[] = {[1:7]};
  }
  raddr2_cp : coverpoint raddr2 {
    bins reg_zero = {0};
    bins others[] = {[1:7]};
  }
  we_cp : coverpoint we {
    bins idle  = {0};
    bins write = {1};
  }
  we_x_waddr    : cross we_cp, waddr_cp;
  waddr_x_raddr1: cross waddr_cp, raddr1_cp;
endgroup
```
