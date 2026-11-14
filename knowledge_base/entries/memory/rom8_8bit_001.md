---
id: "rom8_8bit_001"
context.module: "ROM8"
context.data_width: 8
context.type: "8-entry ROM"
signals: ["addr", "dout"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the ROM being read at every address including the first and last entries, and confirm the returned data spans the zero, mid-range, and maximum stored values.

## Notes
(none)

## RTL
```verilog
module rom8(addr, dout);
  input [2:0] addr;
  output reg [7:0] dout;
  always @(*) begin
    case (addr)
      3'd0: dout = 8'h00;
      3'd1: dout = 8'h11;
      3'd2: dout = 8'h22;
      3'd3: dout = 8'h33;
      3'd4: dout = 8'h44;
      3'd5: dout = 8'h55;
      3'd6: dout = 8'h66;
      3'd7: dout = 8'hFF;
    endcase
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_rom8 (ref logic [2:0] addr, ref logic [7:0] dout);
  addr_cp : coverpoint addr {
    bins entry[] = {[0:7]};
  }
  dout_cp : coverpoint dout {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  addr_x_dout : cross addr_cp, dout_cp;
endgroup
```
