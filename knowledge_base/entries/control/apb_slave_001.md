---
id: "apb_slave_001"
context.module: "APB_SLAVE"
context.data_width: 8
context.type: "APB slave interface"
signals: ["clk", "rst_n", "psel", "penable", "pwrite", "paddr", "pwdata", "prdata", "pready"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the APB slave through its idle, setup, and access phases, both read and write transfers, the ready signal inserting wait states, and the address range covered on both transfer types.

## Notes
(none)

## RTL
```verilog
module apb_slave(clk, rst_n, psel, penable, pwrite, paddr, pwdata, prdata, pready);
  input clk, rst_n, psel, penable, pwrite;
  input [3:0] paddr;
  input [7:0] pwdata;
  output reg [7:0] prdata;
  output pready;
  reg [7:0] mem [0:15];
  assign pready = psel && penable;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) prdata <= 8'b0;
    else if (psel && penable) begin
      if (pwrite) mem[paddr] <= pwdata;
      else        prdata     <= mem[paddr];
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_apb (ref logic psel, penable, pwrite, pready, ref logic [3:0] paddr) @(posedge clk);
  phase_cp : coverpoint {psel, penable} {
    bins idle   = {2'b00};
    bins setup  = {2'b10};
    bins access = {2'b11};
    illegal_bins bad = {2'b01};
  }
  pwrite_cp : coverpoint pwrite {
    bins read  = {0};
    bins write = {1};
  }
  paddr_cp : coverpoint paddr {
    bins first = {0};
    bins mid   = {[1:14]};
    bins last  = {15};
  }
  pready_cp : coverpoint pready {
    bins wait_state = {0};
    bins ready      = {1};
  }
  phase_trans_cp : coverpoint {psel, penable} {
    bins idle_to_setup   = (2'b00 => 2'b10);
    bins setup_to_access = (2'b10 => 2'b11);
    bins access_to_idle  = (2'b11 => 2'b00);
  }
  phase_x_write : cross phase_cp, pwrite_cp;
  addr_x_write  : cross paddr_cp, pwrite_cp;
endgroup
```
